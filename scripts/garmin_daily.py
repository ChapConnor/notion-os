"""Daily wrapper: makes the vault Garmin sync unkillable-by-gap and loud-on-death.

launchd never invokes sync.py directly — only this wrapper (§2.1.2). It owns
the one shared blocking flock around every sync.py invocation, so the Monday
coalesced wake (07:15 + 07:40 firing together) can never race
notes.write_daily's read-truncate-rewrite.

CLI:
  garmin_daily.py             normal daily run
  garmin_daily.py --force     bypass the freshness skip
  garmin_daily.py --sync-dir  override the _sync location (testing)
"""
from __future__ import annotations

import argparse
import fcntl
import json
import logging
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import cfg
import fsio
from notify import notify

ROOT = cfg.ROOT
STATE_DIR = ROOT / "state"
LOCK_PATH = STATE_DIR / "garmin-sync.lock"
DAILY_STATE = STATE_DIR / "daily-state.json"
AUTH_DEAD = STATE_DIR / "auth-dead.json"
ROLLUP_STATE = STATE_DIR / "rollup-state.json"
DEADMAN_STATE = STATE_DIR / "deadman-state.json"

FRESH_HOURS = 6
GAP_FILL_CAP = 14
SINCE_LOOKBACK_D = 2
AUTH_RENOTIFY_D = 3
WEEKLY_STALE_D = 9
MACHINE_OFF_GRACE_D = 2

# Only GarminConnectAuthenticationError produces the friendly string; lockout/
# MFA/SSO deaths arrive as raw tracebacks — classify on substrings (§2.1.2).
AUTH_SUSPECT = (
    "Authentication failed",
    "GarminConnectAuthenticationError",
    "TooManyRequests",
    "Too many login attempts",
    "MFA",
    "Login failed",
)

GARMIN_RUNBOOK = (
    "Runbook 'Garmin token death' (README §2.5.1): lockout wording → wait ~1h; "
    "password changed → edit ~/.config/notion-os/garmin.env; then sync.py --reauth."
)

log = logging.getLogger("garmin_daily")


def _setup_logging() -> None:
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "garmin_daily.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _sync_dir(override: str | None = None) -> Path:
    if override:
        return Path(override)
    return Path(cfg.load()["paths"]["garmin_sync"])


def _read_last_sync(sync_dir: Path) -> datetime | None:
    data = fsio.read_json(sync_dir / "last_sync.json", {}) or {}
    raw = data.get("last_sync")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _is_fresh(last: datetime | None) -> bool:
    if last is None:
        return False
    now = datetime.now(last.tzinfo)
    return last.date() == now.date() and (now - last) < timedelta(hours=FRESH_HOURS)


def _sync_args(last: datetime | None) -> list[str]:
    """Gap chooser: ≤14 days → default gap-fill; >14 → --since last_sync − 2d."""
    if last is None:
        return []
    gap = (date.today() - last.date()).days
    if gap <= GAP_FILL_CAP:
        return []
    since = last.date() - timedelta(days=SINCE_LOOKBACK_D)
    return ["--since", since.isoformat()]


def run_vault_sync(force: bool = False, sync_dir_override: str | None = None) -> tuple[bool, str]:
    """Run sync.py under the shared blocking flock. Returns (ok, output).

    ok=True includes the freshness skip (the vault is current either way).
    Also the entry point weekly_rollup.py uses for its step-0 freshen.
    """
    sync_dir = _sync_dir(sync_dir_override)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # blocking by design
        last = _read_last_sync(sync_dir)
        if not force and _is_fresh(last):
            log.info("freshness skip: last_sync %s (<%dh)", last, FRESH_HOURS)
            return True, "freshness-skip"
        python = sync_dir / ".venv" / "bin" / "python"
        script = sync_dir / "sync.py"
        cmd = [str(python), str(script), *_sync_args(last)]
        log.info("running: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd, cwd=sync_dir, capture_output=True, text=True, timeout=1800
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"{type(exc).__name__}: {exc}"
        output = proc.stdout + proc.stderr
        for line in output.strip().splitlines():
            log.info("sync.py: %s", line)
        return proc.returncode == 0, output


def _is_auth_suspect(output: str) -> bool:
    return any(s in output for s in AUTH_SUSPECT)


def _handle_auth_dead(sync_dir: Path) -> bool:
    """Returns True when the daily retry must be skipped (auth_dead active)."""
    flag = fsio.read_json(AUTH_DEAD)
    if not flag:
        return False
    # Self-clear when last_sync.json advances past the flag.
    last = _read_last_sync(sync_dir)
    if last is not None and last.isoformat() != flag.get("last_sync_at_set"):
        log.info("auth-dead flag self-cleared: last_sync advanced")
        AUTH_DEAD.unlink(missing_ok=True)
        return False
    last_notified = date.fromisoformat(flag["last_notified"])
    if (date.today() - last_notified).days >= AUTH_RENOTIFY_D:
        notify("Garmin auth still dead", GARMIN_RUNBOOK)
        flag["last_notified"] = date.today().isoformat()
        fsio.write_json(AUTH_DEAD, flag)
    log.info("auth-dead flag active — skipping credential retry")
    return True


def _record_failure(state: dict, output: str, sync_dir: Path) -> None:
    if _is_auth_suspect(output):
        # Immediate, skips the 3-strike grace; stop the daily retry so a
        # locked-out account is never driven deeper at 3 logins/day.
        notify("Garmin sync: authentication failure", GARMIN_RUNBOOK)
        last = _read_last_sync(sync_dir)
        fsio.write_json(
            AUTH_DEAD,
            {
                "set_at": datetime.now().isoformat(timespec="seconds"),
                "last_sync_at_set": last.isoformat() if last else None,
                "last_notified": date.today().isoformat(),
            },
        )
        return
    state["consec_failures"] = state.get("consec_failures", 0) + 1
    if state["consec_failures"] >= 3:
        notify(
            "Garmin daily sync failing",
            f"{state['consec_failures']} consecutive failures. "
            f"Last error tail: {output.strip()[-160:]}",
        )


def _watch_weekly_jobs(state: dict) -> None:
    """Meta-watchdog over rollup + deadman state (§2.0).

    Missing state file → silent (the watched job hasn't succeeded yet — keeps
    build-weekend hand-runs from firing spurious notifications). Stale >9d →
    one notification per staleness episode. Suppressed entirely when this
    machine itself was off (our own previous attempt is old too).
    """
    prev_attempt = state.get("last_attempt")
    if prev_attempt:
        prev = datetime.fromisoformat(prev_attempt)
        if datetime.now() - prev > timedelta(days=MACHINE_OFF_GRACE_D):
            log.info("machine-off grace: suppressing weekly staleness checks this run")
            return
    notified: dict = state.setdefault("watch_notified", {})
    for name, path in (("weekly-rollup", ROLLUP_STATE), ("deadman", DEADMAN_STATE)):
        data = fsio.read_json(path)
        if not data or not data.get("last_success"):
            continue  # tolerated silently until first success
        stamp = data["last_success"]
        age = datetime.now() - datetime.fromisoformat(stamp)
        if age > timedelta(days=WEEKLY_STALE_D):
            if notified.get(name) != stamp:
                notify(
                    f"{name} job looks dead",
                    f"Its state is {age.days} days old. Check launchd + "
                    f"~/Library/Logs/notion-os/, or hand-run the script.",
                )
                notified[name] = stamp
        else:
            notified.pop(name, None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily Garmin vault sync wrapper")
    parser.add_argument("--force", action="store_true", help="Bypass freshness skip")
    parser.add_argument("--sync-dir", help="Override _sync location (testing)")
    args = parser.parse_args()

    _setup_logging()
    sync_dir = _sync_dir(args.sync_dir)
    state = fsio.read_json(DAILY_STATE, {}) or {}

    if not _handle_auth_dead(sync_dir):
        ok, output = run_vault_sync(force=args.force, sync_dir_override=args.sync_dir)
        if ok:
            state["consec_failures"] = 0
            state["last_success"] = datetime.now().isoformat(timespec="seconds")
            log.info("vault sync ok (%s)", output.strip().splitlines()[-1] if output.strip() else "")
        else:
            _record_failure(state, output, sync_dir)

    _watch_weekly_jobs(state)
    state["last_attempt"] = datetime.now().isoformat(timespec="seconds")
    fsio.write_json(DAILY_STATE, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
