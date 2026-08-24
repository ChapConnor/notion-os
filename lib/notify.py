"""macOS notifications: osascript, always mirrored to the log, per-run dedupe.

Every notify is also written to the log file — a silently-denied osascript
channel must never be the only record (§2.0's 87-day lesson).
"""
from __future__ import annotations

import logging
import subprocess

log = logging.getLogger(__name__)

_sent_this_run: set[tuple[str, str]] = set()


def notify(title: str, message: str) -> None:
    key = (title, message)
    if key in _sent_this_run:
        return
    _sent_this_run.add(key)
    log.warning("NOTIFY [%s] %s", title, message)
    script = 'display notification "{}" with title "{}"'.format(
        message.replace("\\", "\\\\").replace('"', '\\"'),
        title.replace("\\", "\\\\").replace('"', '\\"'),
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.error("osascript notification failed: %s", exc)
