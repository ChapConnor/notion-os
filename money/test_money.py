"""Unit fixtures for the money pipeline. Run: python money/test_money.py

The load-bearing one: the loader must REJECT a ruleset where TRANSFER is
ordered above E-TRANSFER IN (the shadow-rule that would silently vanish
every incoming e-transfer from Income), and must ACCEPT the real seed.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules as rules_mod
from parsers import parse_amount

REPO = Path(__file__).resolve().parents[1]
CATEGORIES = REPO / "config" / "categories.yml"

BAD_ORDER = """
categories: ["Income — Other", "Transfer — Internal", Uncategorized]
rules:
  - { match: "TRANSFER",      category: "Transfer — Internal" }
  - { match: "E-TRANSFER IN", category: "Income — Other", sign: "+" }
"""

UNKNOWN_CATEGORY = """
categories: [Groceries, Uncategorized]
rules:
  - { match: "LOBLAWS", category: "Grocery" }
"""


def expect_reject(yaml_text: str, needle: str, label: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
        f.write(yaml_text)
        p = Path(f.name)
    try:
        rules_mod.load_rules(p)
    except SystemExit as exc:
        assert needle in str(exc), f"{label}: wrong message: {exc}"
        print(f"  ok  {label} rejected: {str(exc)[:70]}…")
        return
    finally:
        p.unlink()
    raise AssertionError(f"{label}: loader ACCEPTED a broken ruleset")


def main() -> int:
    # 1. The e-transfer ordering pair, proven against a hostile fixture.
    expect_reject(BAD_ORDER, "shadows", "TRANSFER-above-E-TRANSFER-IN")
    expect_reject(UNKNOWN_CATEGORY, "unknown category", "unknown-category")

    # 2. The real committed seed must load clean.
    cats, ruleset = rules_mod.load_rules(CATEGORIES)
    assert len(cats) == 23, f"taxonomy is {len(cats)} categories, want 23"
    print(f"  ok  real seed loads: {len(cats)} categories, {len(ruleset)} rules")

    # 3. Categorization spot checks on the seed.
    c = lambda d, a, acct="RBC Chequing": rules_mod.categorize(d, a, acct, ruleset)
    assert c("INTERAC E-TRANSFER IN JOHN", +500) == "Income — Other"
    assert c("INTERAC E-TRANSFER SENT", -500) == "Transfer — Internal"
    assert c("TRANSFER TO SAVINGS", -100) == "Transfer — Internal"
    assert c("UBEREATS VANCOUVER", -30) == "Dining"
    assert c("UBER TRIP HELP.UBER.COM", -18) == "Transport"
    assert c("SHAW CABLESYSTEMS", -110) == "Phone"
    assert c("PAYROLL DEPOSIT ACME", +4200) == "Income — Salary"
    assert c("PAYROLL CORRECTION", -200) == "Uncategorized"  # sign guard holds
    assert c("RBC DIRECT INVESTING TFSA CONTRIB", -1000) == "Contribution — TFSA"
    assert c("RBC DIRECT INVESTING", -1000) == "Contribution — Taxable"
    assert c("TFSA WITHDRAWAL", +1000) == "Uncategorized"  # inflow ≠ contribution
    assert c("PAYMENT - THANK YOU", +840, "RBC CC") == "Transfer — CC Payment"
    assert c("SOME NEW MERCHANT", -12) == "Uncategorized"
    print("  ok  13 categorization spot checks")

    # 3.5 The real 2026 Scotia 7-col shape: direction column, pending skip.
    from parsers import parse_file

    scotia = (
        "Filter,Date,Description,Sub-description,Status,Type of Transaction,Amount\n"
        '"Current and last statement period","2026-08-24","golf town #54",,"pending","Debit","498.36"\n'
        '"Current and last statement period","2026-08-20","NETFLIX.COM",,"posted","Debit","20.99"\n'
        '"Current and last statement period","2026-08-19","PAYMENT - THANK YOU",,"posted","Credit","840.00"\n'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write(scotia)
        sp = Path(f.name)
    profile = {
        "confirmed": True, "shape": "scotia-7col",
        "fingerprint": "Filter,Date,Description,Sub-description,Status,Type of Transaction,Amount",
        "date_format": "%Y-%m-%d", "sign_multiplier": 1, "account_type": None,
    }
    parsed = parse_file(sp, "scotia-visa", profile)
    sp.unlink()
    assert len(parsed) == 2, f"pending row not skipped: {len(parsed)}"
    assert parsed[0].amount == -20.99 and parsed[0].description == "NETFLIX.COM"
    assert parsed[1].amount == +840.00
    print("  ok  scotia-7col: debit→negative, credit→positive, pending skipped")

    # 4. parse_amount ports the lighthouse lessons.
    assert parse_amount("$1,234.56") == 1234.56
    assert parse_amount("(1,234.56)") == -1234.56
    assert parse_amount("-$5.00") == -5.0
    assert parse_amount("﻿42.00") == 42.0
    assert parse_amount("CAD 99.10") == 99.10
    assert parse_amount("") is None
    assert parse_amount("N/A") is None
    print("  ok  parse_amount")

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
