"""Weekly health-spine rollup: vault → Weekly Log, in the ratified §2.1.3 order.

Steps: (0) lock + freshen the vault  (1) target weeks  (2) pure-local vault
aggregation  (3) Interactions self-heal  (3.5) offline-capture replay
(4) Social Touches by one date-range query  (5) full-row trailing-window
upsert  (6) people-cache export  (7) watchdog in a finally-block.

Every step is idempotent — a run killed anywhere reconverges next run with
zero cleanup.

CLI:
  weekly_rollup.py                    normal Monday run
  weekly_rollup.py --dry-run          print plan/aggregates, write nothing
  weekly_rollup.py --backfill 2025-W01  one-time historical backfill
"""
from __future__ import annotations

import argparse
import fcntl
import logging
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "scripts"))

import cfg
import fsio
import notion_api as napi
import weeks
from notify import notify

log = logging.getLogger("weekly_rollup")

TRAILING_WEEKS = 4
TARGET_CAP = 12
DELTA_WALKBACK_WEEKS = 104
VAULT_STALE_D = 7
DAILY_STATE_STALE_D = 3
DEAD_LETTER_AFTER = 3

ROLLUP_STATE = REPO / "state" / "rollup-state.json"
REPLAYED_UUIDS = REPO / "state" / "replayed-uuids.json"
PENDING_ATTEMPTS = REPO / "state" / "pending-attempts.json"
LOCK_PATH = REPO / "state" / "weekly-rollup.lock"

METRIC_EXCLUDE = {"date", "source"}


# ---------------------------------------------------------------- vault side

def _sync_module_path(config: dict) -> Path:
    return Path(config["paths"]["garmin_sync"])


def _load_sync_helpers(config: dict):
    """Import the parser that wrote the corpus — definitionally the correct reader."""
    sys.path.insert(0, str(_sync_module_path(config)))
    import notes  # noqa: PLC0415

    return notes


def _daily_frontmatter(notes, garmin_dir: Path, d: date) -> dict | None:
    path = notes.daily_path(garmin_dir, d)
    if not path.exists():
        return None
    fm, _ = notes.parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm if isinstance(fm, dict) else None


def _load_activities(notes, garmin_dir: Path) -> list[dict]:
    acts_dir = garmin_dir / "activities"
    if not acts_dir.is_dir():
        return []
    out = []
    for p in sorted(acts_dir.glob("*.md")):
        fm, _ = notes.parse_frontmatter(p.read_text(encoding="utf-8"))
        if isinstance(fm, dict) and fm.get("date"):
            out.append(fm)
    return out


def _num(x: Any) -> float | None:
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _mean(values: list[float], ndigits: int = 1) -> float | None:
    vals = [v for v in values if v is not None]
    return round(statistics.mean(vals), ndigits) if vals else None


def _week_weight_avg(notes, garmin_dir: Path, key: str) -> float | None:
    vals = []
    for d in weeks.week_days(key):
        fm = _daily_frontmatter(notes, garmin_dir, d)
        if fm:
            w = _num(fm.get("weight_kg"))
            if w is not None:
                vals.append(w)
    return _mean(vals)


def aggregate_week(
    notes, garmin_dir: Path, key: str, activities: list[dict], pt_types: list[str]
) -> dict[str, Any]:
    days = weeks.week_days(key)
    days_with_data = 0
    weight, sleep, score, rhr, hrv = [], [], [], [], []
    for d in days:
        fm = _daily_frontmatter(notes, garmin_dir, d)
        if not fm:
            continue
        if any(k not in METRIC_EXCLUDE and fm.get(k) is not None for k in fm):
            days_with_data += 1
        w = _num(fm.get("weight_kg"))
        if w is not None:
            weight.append(w)
        # Sleep coalesce per Years.md: sleep_hours ?? sleep_hours_inferred
        s = _num(fm.get("sleep_hours"))
        if s is None:
            s = _num(fm.get("sleep_hours_inferred"))
        if s is not None:
            sleep.append(s)
        sc = _num(fm.get("sleep_score"))
        if sc is not None:
            score.append(sc)
        r = _num(fm.get("resting_hr"))
        if r is not None:
            rhr.append(r)
        h = _num(fm.get("hrv_last_night_avg"))
        if h is not None:
            hrv.append(h)

    start, end = days[0], days[-1]
    week_acts = [a for a in activities if start <= _act_date(a) <= end]
    training_load = sum(v for a in week_acts if (v := _num(a.get("training_load"))) is not None)
    pt = sum(1 for a in week_acts if a.get("type") in pt_types)

    weight_avg = _mean(weight)
    # Weight Delta walks back to the most recent prior non-blank week.
    delta = None
    if weight_avg is not None:
        prev_key = weeks.prev_week_key(key)
        for _ in range(DELTA_WALKBACK_WEEKS):
            prev_avg = _week_weight_avg(notes, garmin_dir, prev_key)
            if prev_avg is not None:
                delta = round(weight_avg - prev_avg, 1)
                break
            prev_key = weeks.prev_week_key(prev_key)

    return {
        "Week": key,
        "Week Start": start.isoformat(),
        "Weight Avg": weight_avg,
        "Weight Delta": delta,
        "Training Sessions": len(week_acts) or 0,
        "Training Load": round(training_load, 1) if week_acts else 0,
        "PT Sessions": pt,
        "Sleep Avg": _mean(sleep),
        "Sleep Score": _mean(score),
        "RHR": _mean(rhr),
        "HRV": _mean(hrv),
        "Days With Data": days_with_data,
        # Social Touches merged in later from the Notion query.
    }


def _act_date(a: dict) -> date:
    d = a.get("date")
    if isinstance(d, date):
        return d
    try:
        return date.fromisoformat(str(d))
    except ValueError:
        return date(1970, 1, 1)


# ---------------------------------------------------------------- notion side

def heal_interactions(client: napi.Notion, db_id: str, dry_run: bool) -> int:
    """Empty Date := created_time; blank title := 'MMM D · Type'. Before counting."""
    healed = 0
    for page in client.query_db(db_id, filter={"property": "Date", "date": {"is_empty": True}}):
        created = page["created_time"][:10]
        if not dry_run:
            client.update_page(page["id"], {"Date": napi.date_prop(created)})
        healed += 1
        log.info("healed empty Date -> %s on %s", created, page["id"])
    for page in client.query_db(db_id, filter={"property": "Name", "title": {"is_empty": True}}):
        d = napi.read_date(page, "Date") or page["created_time"][:10]
        typ = napi.read_select(page, "Type") or "1:1"
        day = date.fromisoformat(d[:10])
        name = f"{day.strftime('%b')} {day.day} · {typ}"
        if not dry_run:
            client.update_page(page["id"], {"Name": napi.title(name)})
        healed += 1
        log.info("healed blank title -> %r on %s", name, page["id"])
    return healed


def replay_pending(
    client: napi.Notion, config: dict, db_id: str, dry_run: bool
) -> tuple[int, int]:
    """Replay offline captures from the Shortcut's iCloud pending/ folder.

    Contract (§2.1.8): pending/<uuid>.json holds {uuid, date, people: [page-id…],
    type}; the create echoes the uuid in the page body (exact dedupe key), the
    file is deleted on success, and a file that fails 3 Mondays dead-letters
    with one notification.
    """
    container = Path(config["paths"]["shortcuts_container"])
    pending_dir = container / "pending"
    if not pending_dir.is_dir():
        return 0, 0
    replayed: list = fsio.read_json(REPLAYED_UUIDS, []) or []
    attempts: dict = fsio.read_json(PENDING_ATTEMPTS, {}) or {}
    ok = failed = 0
    for f in sorted(pending_dir.glob("*.json")):
        payload = fsio.read_json(f)
        uuid = (payload or {}).get("uuid") or f.stem
        try:
            if uuid not in replayed:
                if dry_run:
                    log.info("[dry-run] would replay %s", f.name)
                    continue
                client.create_page(
                    db_id,
                    {
                        "Date": napi.date_prop(str(payload["date"])[:10]),
                        "People": napi.relation(list(payload["people"])),
                        "Type": napi.select(payload.get("type", "1:1")),
                    },
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"text": {"content": f"capture-uuid: {uuid}"}}
                                ]
                            },
                        }
                    ],
                )
                replayed.append(uuid)
                fsio.write_json(REPLAYED_UUIDS, replayed)
            f.unlink()
            attempts.pop(f.name, None)
            ok += 1
        except (KeyError, TypeError, ValueError, napi.NotionAbort) as exc:
            if isinstance(exc, napi.NotionAbort):
                raise  # API-level aborts stay loud — never swallowed
            failed += 1
            n = attempts.get(f.name, 0) + 1
            attempts[f.name] = n
            log.warning("pending replay failed for %s (attempt %d): %s", f.name, n, exc)
            if n >= DEAD_LETTER_AFTER:
                dead = pending_dir / "dead-letter"
                dead.mkdir(exist_ok=True)
                f.rename(dead / f.name)
                attempts.pop(f.name, None)
                notify(
                    "Offline capture dead-lettered",
                    f"{f.name} failed {DEAD_LETTER_AFTER} Mondays — moved to "
                    f"pending/dead-letter/ for hand repair.",
                )
    fsio.write_json(PENDING_ATTEMPTS, attempts)
    return ok, failed


def social_touches(
    client: napi.Notion, db_id: str, keys: list[str]
) -> dict[str, int]:
    """One date-range query spanning all target weeks, bucketed locally."""
    lo = weeks.week_start(keys[0]).isoformat()
    hi = weeks.week_end(keys[-1]).isoformat()
    counts = {k: 0 for k in keys}
    q = {
        "and": [
            {"property": "Date", "date": {"on_or_after": lo}},
            {"property": "Date", "date": {"on_or_before": hi}},
        ]
    }
    for page in client.query_db(db_id, filter=q):
        d = napi.read_date(page, "Date")
        if not d:
            continue
        k = weeks.week_key(date.fromisoformat(d[:10]))
        if k in counts:
            counts[k] += 1
    return counts


def upsert_weeks(
    client: napi.Notion, db_id: str, rows: list[dict], dry_run: bool
) -> tuple[int, int]:
    """One compound title-equals query, then per-week full-row create/update.

    The full row is rewritten for every trailing week — blanks as explicit
    nulls — so late sleep data and late-logged touches converge (§2.1.3.5).
    """
    existing: dict[str, str] = {}
    key_filter = {"or": [{"property": "Week", "title": {"equals": r["Week"]}} for r in rows]}
    for page in client.query_db(db_id, filter=key_filter):
        existing[napi.read_title(page, "Week")] = page["id"]

    created = updated = 0
    for r in rows:
        props = {
            "Week": napi.title(r["Week"]),
            "Week Start": napi.date_prop(r["Week Start"]),
            "Weight Avg": napi.number(r["Weight Avg"]),
            "Weight Delta": napi.number(r["Weight Delta"]),
            "Training Sessions": napi.number(r["Training Sessions"]),
            "Training Load": napi.number(r["Training Load"]),
            "PT Sessions": napi.number(r["PT Sessions"]),
            "Sleep Avg": napi.number(r["Sleep Avg"]),
            "Sleep Score": napi.number(r["Sleep Score"]),
            "RHR": napi.number(r["RHR"]),
            "HRV": napi.number(r["HRV"]),
            "Social Touches": napi.number(r["Social Touches"]),
            "Days With Data": napi.number(r["Days With Data"]),
        }
        if dry_run:
            action = "update" if r["Week"] in existing else "create"
            log.info("[dry-run] would %s %s: %s", action, r["Week"], _fmt_row(r))
            continue
        if r["Week"] in existing:
            client.update_page(existing[r["Week"]], props)
            updated += 1
        else:
            client.create_page(db_id, props)
            created += 1
    return created, updated


def _fmt_row(r: dict) -> str:
    return (
        f"days={r['Days With Data']} sleep={r['Sleep Avg']} score={r['Sleep Score']} "
        f"rhr={r['RHR']} hrv={r['HRV']} acts={r['Training Sessions']} "
        f"load={r['Training Load']} pt={r['PT Sessions']} touches={r['Social Touches']} "
        f"wt={r['Weight Avg']} Δ={r['Weight Delta']}"
    )


def export_people_cache(
    client: napi.Notion, config: dict, db_id: str, dry_run: bool
) -> int:
    """People DB → tier-sorted notion-people.json in the Shortcuts container."""
    tier_rank = {"A": 0, "B": 1, "C": 2}
    people = []
    for page in client.query_db(db_id):
        people.append(
            {
                "name": napi.read_title(page, "Name"),
                "id": page["id"],
                "tier": napi.read_select(page, "Tier"),
            }
        )
    people.sort(key=lambda p: (tier_rank.get(p["tier"], 3), p["name"].lower()))
    container = Path(config["paths"]["shortcuts_container"])
    if dry_run:
        log.info("[dry-run] would export %d people to %s", len(people), container)
        return len(people)
    if not container.is_dir():
        raise RuntimeError(
            f"Shortcuts container missing: {container} — is iCloud Drive for "
            "Shortcuts enabled on this Mac?"
        )
    fsio.write_json(container / "notion-people.json", people)
    return len(people)


# ---------------------------------------------------------------- orchestration

def pick_targets(backfill_from: str | None, today: date) -> tuple[list[str], bool]:
    """Target weeks; True when the cap forced truncation."""
    last_completed = weeks.last_completed_week_key(today)
    if backfill_from:
        return weeks.completed_weeks_between(backfill_from, today), False
    targets = set()
    cur = last_completed
    for _ in range(TRAILING_WEEKS):
        targets.add(cur)
        cur = weeks.prev_week_key(cur)
    state = fsio.read_json(ROLLUP_STATE, {}) or {}
    last_week = state.get("last_week")
    if last_week:
        try:
            targets.update(weeks.completed_weeks_between(last_week, today))
        except ValueError:
            pass
    ordered = sorted(targets, key=weeks.week_start)
    if len(ordered) > TARGET_CAP:
        return ordered[-TARGET_CAP:], True
    return ordered, False


def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly Log rollup")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backfill", metavar="YYYY-Www")
    args = parser.parse_args()

    log_dir = REPO / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "weekly_rollup.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    config = cfg.load()
    ids = config["notion"]["db_ids"]
    failures: list[str] = []
    rows: list[dict] = []
    core_ok = False
    today = date.today()

    (REPO / "state").mkdir(exist_ok=True)
    with open(LOCK_PATH, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            # (0) freshen — flag-and-continue on failure
            from garmin_daily import run_vault_sync  # noqa: PLC0415

            sync_ok, _ = run_vault_sync()
            if not sync_ok:
                failures.append("vault freshen failed — aggregating what the vault has")

            # (1) targets
            targets, capped = pick_targets(args.backfill, today)
            if capped:
                notify(
                    "Rollup gap exceeds cap",
                    f"More than {TARGET_CAP} weeks pending. Run "
                    f"weekly_rollup.py --backfill <first-missing-week>.",
                )
            log.info("target weeks (%d): %s → %s", len(targets), targets[0], targets[-1])

            # (2) pure-local aggregation
            notes = _load_sync_helpers(config)
            garmin_dir = _sync_module_path(config).parent
            activities = _load_activities(notes, garmin_dir)
            pt_types = list(config["health"]["pt_type_allowlist"])
            rows = [
                aggregate_week(notes, garmin_dir, k, activities, pt_types)
                for k in targets
            ]

            client = napi.Notion()

            # (3) self-heal before counting
            healed = heal_interactions(client, ids["interactions"], args.dry_run)

            # (3.5) offline replay
            replayed, replay_failed = replay_pending(
                client, config, ids["interactions"], args.dry_run
            )

            # (4) social touches
            touches = social_touches(client, ids["interactions"], targets)
            for r in rows:
                r["Social Touches"] = touches.get(r["Week"], 0)

            # (5) upsert
            created, updated = upsert_weeks(client, ids["weekly_log"], rows, args.dry_run)

            # (6) people cache
            people_count = export_people_cache(client, config, ids["people"], args.dry_run)

            core_ok = True
            print(
                f"{'[dry-run] ' if args.dry_run else ''}"
                f"weeks={len(rows)} created={created} updated={updated} "
                f"healed={healed} replayed={replayed} replay_failed={replay_failed} "
                f"people_cached={people_count}"
            )
            if not args.dry_run:
                fsio.write_json(
                    ROLLUP_STATE,
                    {
                        "last_success": datetime.now().isoformat(timespec="seconds"),
                        "last_week": weeks.last_completed_week_key(today),
                    },
                )
        except Exception as exc:  # noqa: BLE001 — watchdog boundary
            failures.append(f"{type(exc).__name__}: {exc}")
            log.exception("rollup step failed")
        finally:
            # (7) watchdog — §2.1.3 step 7, always runs
            try:
                if failures:
                    notify("Weekly rollup failed", "; ".join(failures)[:230])
                if core_ok and not args.backfill and not args.dry_run:
                    last_key = weeks.last_completed_week_key(today)
                    last_row = next((r for r in rows if r["Week"] == last_key), None)
                    if last_row and last_row["Days With Data"] == 0:
                        notify(
                            "Weekly Log: zero data days",
                            f"{last_key} has Days With Data = 0 — upstream Garmin "
                            f"sync presumed dead. " ,
                        )
                notes_dir = _sync_module_path(config).parent / "daily"
                newest = max(
                    (p.stem for p in notes_dir.glob("*-*-*.md")), default=None
                )
                if newest and (today - date.fromisoformat(newest)).days > VAULT_STALE_D:
                    notify("Vault stale", f"Newest daily note is {newest} (> {VAULT_STALE_D}d old).")
                daily_state = fsio.read_json(REPO / "state" / "daily-state.json", {}) or {}
                attempt = daily_state.get("last_attempt")
                if attempt and (
                    datetime.now() - datetime.fromisoformat(attempt)
                ) > timedelta(days=DAILY_STATE_STALE_D):
                    notify(
                        "Daily Garmin job looks dead",
                        f"garmin_daily last attempted {attempt} (> {DAILY_STATE_STALE_D}d).",
                    )
            except Exception:  # noqa: BLE001
                log.exception("watchdog itself failed")

    return 0 if core_ok else 1


if __name__ == "__main__":
    sys.exit(main())
