"""Gated Monthly Money → exports/monthly_money.csv (§1.5).

Exactly the 16 columns in CSV order, Month asc. Months with a blank Net
Worth are skipped — the export gate IS the completeness guard. Atomic
tmp+rename so an open Excel never sees a torn file. Reading the three
formula properties here is §1.10-legal (deadman/export are the exceptions).
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

EXPORT_COLUMNS = [
    "Month", "Income", "Spend", "Surplus", "Savings Rate",
    "Contrib TFSA", "Contrib RRSP", "Contrib FHSA", "Contrib Taxable",
    "Bal Chequing", "Bal TFSA", "Bal RRSP", "Bal FHSA", "Bal Taxable",
    "Liabilities", "Net Worth",
]


def _formula_number(page: dict, prop: str):
    f = page["properties"][prop].get("formula") or {}
    return f.get("number")


def _number(page: dict, prop: str):
    return page["properties"][prop].get("number")


def _title(page: dict, prop: str) -> str:
    return "".join(t.get("plain_text", "") for t in page["properties"][prop]["title"])


def month_rows(client, mm_db_id: str) -> list[dict]:
    """All Monthly Money rows as flat dicts keyed by export column name."""
    rows = []
    for page in client.query_db(mm_db_id):
        rows.append(
            {
                "Month": _title(page, "Month"),
                "Income": _number(page, "Income"),
                "Spend": _number(page, "Spend"),
                "Surplus": _formula_number(page, "Surplus"),
                "Savings Rate": _formula_number(page, "Savings Rate"),
                "Contrib TFSA": _number(page, "Contrib TFSA"),
                "Contrib RRSP": _number(page, "Contrib RRSP"),
                "Contrib FHSA": _number(page, "Contrib FHSA"),
                "Contrib Taxable": _number(page, "Contrib Taxable"),
                "Bal Chequing": _number(page, "Bal Chequing"),
                "Bal TFSA": _number(page, "Bal TFSA"),
                "Bal RRSP": _number(page, "Bal RRSP"),
                "Bal FHSA": _number(page, "Bal FHSA"),
                "Bal Taxable": _number(page, "Bal Taxable"),
                "Liabilities": _number(page, "Liabilities"),
                "Net Worth": _formula_number(page, "Net Worth"),
                "_page_id": page["id"],
            }
        )
    return rows


def complete_months(rows: list[dict]) -> list[dict]:
    return sorted(
        (r for r in rows if r["Net Worth"] is not None),
        key=lambda r: r["Month"],
    )


def stamp_map(rows: list[dict]) -> dict:
    """{month: [net_worth, income, spend]} for complete months — the change
    detector that triggers a full regen (§2.1.4)."""
    return {
        r["Month"]: [r["Net Worth"], r["Income"], r["Spend"]]
        for r in complete_months(rows)
    }


def write_export(rows: list[dict], export_path: Path) -> int:
    """Full atomic rewrite of the export CSV. Returns exported month count."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
    import fsio  # noqa: PLC0415

    exportable = complete_months(rows)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for r in exportable:
        writer.writerow(r)
    fsio.write_text(export_path, buf.getvalue())
    return len(exportable)
