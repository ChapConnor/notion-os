"""ISO-week math shared by every script, so they agree by construction (§2.1.6).

Week keys look like `2026-W34` and match Python's date.isocalendar().
"""
from __future__ import annotations

import re
from datetime import date, timedelta

WEEK_KEY_RE = re.compile(r"^(\d{4})-W(\d{2})$")


def week_key(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def parse_week_key(key: str) -> tuple[int, int]:
    m = WEEK_KEY_RE.match(key)
    if not m:
        raise ValueError(f"bad week key {key!r} (want YYYY-Www, e.g. 2025-W01)")
    return int(m.group(1)), int(m.group(2))


def week_start(key: str) -> date:
    """Monday of the ISO week."""
    year, week = parse_week_key(key)
    return date.fromisocalendar(year, week, 1)


def week_end(key: str) -> date:
    """Sunday of the ISO week."""
    return week_start(key) + timedelta(days=6)


def week_days(key: str) -> list[date]:
    start = week_start(key)
    return [start + timedelta(days=i) for i in range(7)]


def prev_week_key(key: str) -> str:
    return week_key(week_start(key) - timedelta(days=1))


def last_completed_week_key(today: date) -> str:
    """The most recent ISO week whose Sunday is strictly before today."""
    monday_this = date.fromisocalendar(*today.isocalendar()[:2], 1)
    return week_key(monday_this - timedelta(days=1))


def completed_weeks_between(first_key: str, today: date) -> list[str]:
    """Every completed week from first_key through the last completed one."""
    last = last_completed_week_key(today)
    keys: list[str] = []
    cur = week_start(first_key)
    stop = week_start(last)
    while cur <= stop:
        keys.append(week_key(cur))
        cur += timedelta(days=7)
    return keys
