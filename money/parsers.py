"""Validation-first bank CSV parsers (§2.1.5).

Formats are never guessed: first contact per format MUST be `inspect`, which
records {shape, fingerprint, date_format, sign_multiplier, account_type,
confirmed} into config/parser_profiles.yml on explicit human confirm. Every
subsequent run re-checks the fingerprint before parsing row 1. Drift, >2%
unparseable rows, a populated USD$ column, or an Account Type mismatch abort
the whole file — before a single Notion write — naming the exact difference.

Ported from lighthouse csv.js: parse_amount (currency symbols, thousands
commas, accounting parens), BOM handling, the local-date lesson (dates are
naive local dates, never timezone-shifted). Explicitly NOT ported from
bank.js: heuristic column detection, deposit-discarding, unordered rules —
each a proven silent-misparse vector.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

RBC_HEADER = (
    '"Account Type","Account Number","Transaction Date","Cheque Number",'
    '"Description 1","Description 2","CAD$","USD$"'
)
RBC_COLUMNS = [
    "Account Type", "Account Number", "Transaction Date", "Cheque Number",
    "Description 1", "Description 2", "CAD$", "USD$",
]
SCOTIA_5COL_COLUMNS = ["Date", "Description", "Debit", "Credit", "Balance"]
# The shape the real 2026 Scotia portal actually emits (found at first contact,
# 2026-08-24): unsigned Amount + Debit/Credit direction column + Status.
SCOTIA_7COL_COLUMNS = [
    "Filter", "Date", "Description", "Sub-description", "Status",
    "Type of Transaction", "Amount",
]
MAX_UNPARSEABLE_FRACTION = 0.02

#: sentinel for rows deliberately skipped (e.g. Scotia "pending" — a pending
#: row can change when it posts, which would break hash stability).
SKIPPED = object()

_AMOUNT_JUNK = re.compile(r"[$€£]|CAD|USD|\s")


class ParserAbort(SystemExit):
    """Whole-file abort. Nothing from this file may reach Notion."""


@dataclass(frozen=True)
class Row:
    raw_line: str
    raw_date: str
    raw_amount: str
    raw_description: str
    date: date
    amount: float
    description: str


def parse_amount(raw: str | None) -> float | None:
    """Currency symbols, thousands commas, accounting parens. None on junk."""
    if raw is None:
        return None
    s = raw.strip().lstrip("﻿")
    if not s:
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = _AMOUNT_JUNK.sub("", s).replace(",", "")
    if not s or s in ("-", "+"):
        return None
    try:
        value = float(s)
    except ValueError:
        return None
    return -value if negative else value


def _normalize_description(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def _read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return [ln for ln in text.splitlines() if ln.strip()]


def _split(line: str) -> list[str]:
    return next(csv.reader(io.StringIO(line)))


def _parse_date(raw: str, fmt: str, path: Path, line_no: int) -> date | None:
    try:
        return datetime.strptime(raw.strip(), fmt).date()
    except ValueError:
        return None


def compute_fingerprint(path: Path) -> tuple[str, str]:
    """(shape, fingerprint) detected from the file itself."""
    lines = _read_lines(path)
    if not lines:
        raise ParserAbort(f"{path.name}: file is empty")
    first_cols = _split(lines[0])
    if first_cols == RBC_COLUMNS:
        return "rbc", lines[0].strip()
    if first_cols == SCOTIA_5COL_COLUMNS:
        return "scotia-5col", lines[0].strip()
    if first_cols == SCOTIA_7COL_COLUMNS:
        return "scotia-7col", lines[0].strip()
    if len(first_cols) == 3 and _parse_any_date(first_cols[0]):
        return "scotia-3col", f"headerless:3col"
    raise ParserAbort(
        f"{path.name}: unrecognized format — first line matches none of the "
        f"known shapes (RBC 8-col, Scotia 5-col, Scotia 7-col, headerless "
        f"3-col). Run `inspect` on it."
    )


def _parse_any_date(raw: str) -> bool:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            datetime.strptime(raw.strip(), fmt)
            return True
        except ValueError:
            continue
    return False


def _require_confirmed(profile: dict, key: str, path: Path) -> None:
    if not profile.get("confirmed"):
        raise ParserAbort(
            f"{path.name}: parser profile '{key}' is not confirmed — run "
            f"`import_transactions.py inspect {path} --account {key}` first. "
            f"Sign conventions are confirmed, never guessed."
        )
    for field in ("fingerprint", "date_format", "sign_multiplier", "shape"):
        if profile.get(field) in (None, ""):
            raise ParserAbort(
                f"{path.name}: profile '{key}' is missing {field!r} — re-run inspect."
            )


def parse_file(path: Path, key: str, profile: dict) -> list[Row]:
    """Parse one drops CSV under a confirmed profile. Aborts whole-file on drift."""
    _require_confirmed(profile, key, path)
    shape, fingerprint = compute_fingerprint(path)
    if shape != profile["shape"] or fingerprint != profile["fingerprint"]:
        raise ParserAbort(
            f"{path.name}: format drift — file is shape={shape!r} "
            f"fingerprint={fingerprint!r} but the confirmed profile has "
            f"shape={profile['shape']!r} fingerprint={profile['fingerprint']!r}. "
            f"Re-run `inspect` to confirm the new format (runbook 'CSV format drift')."
        )
    lines = _read_lines(path)
    headered = shape in ("rbc", "scotia-5col", "scotia-7col")
    body = lines[1:] if headered else lines
    fmt = profile["date_format"]
    sign = float(profile["sign_multiplier"])
    rows: list[Row] = []
    bad: list[str] = []
    skipped_pending = 0
    for i, line in enumerate(body, 2 if headered else 1):
        cols = _split(line)
        parsed = _parse_row(shape, cols, line, i, fmt, sign, key, profile, path)
        if parsed is SKIPPED:
            skipped_pending += 1
            continue
        if parsed is None:
            bad.append(f"line {i}: {line[:80]}")
            continue
        rows.append(parsed)
    if skipped_pending:
        print(
            f"  {path.name}: skipped {skipped_pending} pending row(s) — they "
            f"import once posted (hash stability)"
        )
    if not rows:
        raise ParserAbort(f"{path.name}: zero parseable rows")
    if len(bad) / (len(rows) + len(bad)) > MAX_UNPARSEABLE_FRACTION:
        detail = "\n  ".join(bad[:5])
        raise ParserAbort(
            f"{path.name}: {len(bad)}/{len(rows) + len(bad)} rows unparseable "
            f"(>{MAX_UNPARSEABLE_FRACTION:.0%}) — aborting whole file.\n  {detail}"
        )
    return rows


def _parse_row(
    shape: str,
    cols: list[str],
    line: str,
    line_no: int,
    fmt: str,
    sign: float,
    key: str,
    profile: dict,
    path: Path,
) -> "Row | None | object":
    if shape == "rbc":
        if len(cols) != 8:
            return None
        acct_type, _num, raw_date, _chq, d1, d2, cad, usd = cols
        expected_type = profile.get("account_type")
        if expected_type and acct_type.strip() != expected_type:
            raise ParserAbort(
                f"{path.name} line {line_no}: Account Type {acct_type.strip()!r} "
                f"≠ profile's {expected_type!r} — wrong file dropped under "
                f"'{key}'? The rename IS the account binding; fix the drop."
            )
        if usd.strip() and parse_amount(usd) not in (None, 0.0):
            raise ParserAbort(
                f"{path.name} line {line_no}: USD$ column is populated "
                f"({usd.strip()!r}) — this pipeline is CAD-only by design."
            )
        d = _parse_date(raw_date, fmt, path, line_no)
        amount = parse_amount(cad)
        if d is None or amount is None:
            return None
        return Row(
            raw_line=line,
            raw_date=raw_date.strip(),
            raw_amount=cad.strip(),
            raw_description=_normalize_description(d1, d2),
            date=d,
            amount=round(amount * sign, 2),
            description=_normalize_description(d1, d2),
        )
    if shape == "scotia-3col":
        if len(cols) != 3:
            return None
        raw_date, desc, raw_amt = cols
        d = _parse_date(raw_date, fmt, path, line_no)
        amount = parse_amount(raw_amt)
        if d is None or amount is None:
            return None
        return Row(
            raw_line=line,
            raw_date=raw_date.strip(),
            raw_amount=raw_amt.strip(),
            raw_description=desc.strip(),
            date=d,
            amount=round(amount * sign, 2),
            description=_normalize_description(desc),
        )
    if shape == "scotia-7col":
        if len(cols) != 7:
            return None
        _filter, raw_date, desc, sub_desc, status, tx_type, raw_amt = cols
        if status.strip().lower() == "pending":
            return SKIPPED
        d = _parse_date(raw_date, fmt, path, line_no)
        amount = parse_amount(raw_amt)
        direction = tx_type.strip().lower()
        if d is None or amount is None or direction not in ("debit", "credit"):
            return None
        # The direction column is the authority; magnitude from abs(). The
        # real portal writes debits positive AND credits negative — abs +
        # direction normalizes both quirks to inflow + / outflow −.
        signed = abs(amount) if direction == "credit" else -abs(amount)
        return Row(
            raw_line=line,
            raw_date=raw_date.strip(),
            raw_amount=raw_amt.strip(),
            raw_description=_normalize_description(desc, sub_desc),
            date=d,
            amount=round(signed * sign, 2),
            description=_normalize_description(desc, sub_desc),
        )
    if shape == "scotia-5col":
        if len(cols) != 5:
            return None
        raw_date, desc, debit, credit, _bal = cols
        d = _parse_date(raw_date, fmt, path, line_no)
        deb = parse_amount(debit) or 0.0
        cred = parse_amount(credit) or 0.0
        if d is None or (not debit.strip() and not credit.strip()):
            return None
        return Row(
            raw_line=line,
            raw_date=raw_date.strip(),
            raw_amount=f"{debit.strip()}|{credit.strip()}",
            raw_description=desc.strip(),
            date=d,
            amount=round((cred - deb) * sign, 2),
            description=_normalize_description(desc),
        )
    raise ParserAbort(f"{path.name}: unknown profile shape {shape!r}")
