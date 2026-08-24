"""THE single dead-man switch (§2.1.4). Friday 09:00 via launchd.

One paginated Monthly Money query over a trailing 12-month window floored at
config's system_start_month. Pending = any window month (excluding the
current one) missing or with a blank Net Worth. ONE notification naming all
pending months and their empty balance columns; urgent wording as a month
approaches the 1-year bank-export horizon. Max one notification per week —
no stacking, no escalation (nag fatigue is the documented abandonment
trigger). Regenerates the Excel export on stamp-map change. Its own failure
notifies LOUDER than the nag it replaces.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "money"))

import cfg
import fsio
import mm_export
import notion_api as napi
from notify import notify

STATE_PATH = REPO / "state" / "deadman-state.json"
IMPORT_STATE = REPO / "state" / "import"
EXPORT_PATH = REPO / "exports" / "monthly_money.csv"
WINDOW_MONTHS = 12
STALE_JOURNAL_H = 1

BALANCE_COLS = ["Bal Chequing", "Bal TFSA", "Bal RRSP", "Bal FHSA", "Bal Taxable", "Liabilities"]


def month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def shift_month(key: str, delta: int) -> str:
    y, m = int(key[:4]), int(key[5:7])
    total = y * 12 + (m - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def window_months(today: date, start_floor: str | None) -> list[str]:
    """Trailing 12 completed months, floored at system_start_month."""
    current = month_key(today)
    months = [shift_month(current, -i) for i in range(1, WINDOW_MONTHS + 1)]
    if start_floor:
        months = [m for m in months if m >= start_floor]
    return sorted(months)


def month_age_days(key: str, today: date) -> int:
    y, m = int(key[:4]), int(key[5:7])
    end = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
    return (today - end).days


def check_stale_journals(now: datetime) -> list[str]:
    stale = []
    if IMPORT_STATE.is_dir():
        for jp in IMPORT_STATE.glob("*.json"):
            j = fsio.read_json(jp) or {}
            if j.get("phase") != "done":
                age_h = (now.timestamp() - jp.stat().st_mtime) / 3600
                if age_h > STALE_JOURNAL_H:
                    stale.append(j.get("batch_id", jp.name))
    return stale


def main() -> int:
    config = cfg.load()
    today = date.today()
    now = datetime.now()
    state = fsio.read_json(STATE_PATH, {}) or {}
    try:
        start_floor = config["money"].get("system_start_month")
        if not start_floor:
            print("system_start_month not set (first sitting pending) — dead-man idle by design")
            state["last_success"] = now.isoformat(timespec="seconds")
            fsio.write_json(STATE_PATH, state)
            return 0

        client = napi.Notion()
        rows = mm_export.month_rows(client, config["notion"]["db_ids"]["monthly_money"])
        by_month = {r["Month"]: r for r in rows}

        pending: list[str] = []
        details: list[str] = []
        horizon_d = int(config["money"]["export_horizon_warn_d"])
        urgent = False
        for m in window_months(today, str(start_floor)):
            row = by_month.get(m)
            if row is None:
                pending.append(m)
                details.append(f"{m}: no row (no import yet)")
            elif row["Net Worth"] is None:
                pending.append(m)
                empty = [c for c in BALANCE_COLS if row[c] is None]
                details.append(f"{m}: blank {', '.join(empty) or 'Net Worth'}")
            else:
                continue
            if month_age_days(m, today) > horizon_d:
                urgent = True

        if pending:
            last_nag = state.get("last_nag")
            if not last_nag or (now - datetime.fromisoformat(last_nag)).days >= 7:
                head = "URGENT — bank-export horizon approaching: " if urgent else ""
                notify(
                    "Monthly Money sitting pending",
                    f"{head}{'; '.join(details)[:200]}. Runbook: the monthly "
                    f"sitting (README §7).",
                )
                state["last_nag"] = now.isoformat(timespec="seconds")
        else:
            state.pop("last_nag", None)

        # Export regen on stamp-map change (full atomic rewrite).
        stamps = mm_export.stamp_map(rows)
        if stamps != state.get("stamps"):
            n = mm_export.write_export(rows, EXPORT_PATH)
            state["stamps"] = stamps
            print(f"stamp map changed — export regenerated ({n} months)")
        else:
            print("stamp map unchanged — export untouched")

        stale = check_stale_journals(now)
        if stale:
            notify(
                "Import batch incomplete",
                f"Journal(s) {', '.join(stale)} stuck >1h mid-import — re-run "
                f"import_transactions.py to resume (it converges).",
            )

        print(f"deadman: window={len(window_months(today, str(start_floor)))}m pending={pending or 'none'}")
        state["last_success"] = now.isoformat(timespec="seconds")
        fsio.write_json(STATE_PATH, state)
        return 0
    except BaseException as exc:  # its own failure is louder than the nag
        notify(
            "DEAD-MAN CHECK ITSELF FAILED",
            f"{type(exc).__name__}: {exc} — the money nag is not running; "
            f"hand-run scripts/deadman_check.py.",
        )
        raise


if __name__ == "__main__":
    sys.exit(main())
