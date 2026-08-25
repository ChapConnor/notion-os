"""Monthly transaction import + money-pipeline subcommands (§2.1.5).

  import_transactions.py [import] [--yes]      import all confirmed drops
  import_transactions.py inspect FILE --account KEY   confirm a format
  import_transactions.py re-aggregate YYYY-MM  recompute one month
  import_transactions.py export                regenerate the gated CSV export
  import_transactions.py recategorize          re-rule ONLY Uncategorized rows
  import_transactions.py repair-batch ID --list | --delete

Standing invariants (§2.6): Hash + Import Batch ride in the ONE create call;
Category is written once and never again by any script path except
recategorize-on-Uncategorized; Bal ×5/Liabilities are never script-written;
aggregates always come from post-write Notion queries; the journal is flushed
after every create ack, never before; every path fails loudly or not at all.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "lib"))
sys.path.insert(0, str(REPO / "money"))

import cfg
import fsio
import mm_export
import notion_api as napi
import rules as rules_mod
import yaml
from parsers import ParserAbort, compute_fingerprint, parse_file, parse_amount  # noqa: F401

DROPS = REPO / "drops"
IMPORT_STATE = REPO / "state" / "import"
PROFILES_PATH = REPO / "config" / "parser_profiles.yml"
CATEGORIES_PATH = REPO / "config" / "categories.yml"
EXPORT_PATH = REPO / "exports" / "monthly_money.csv"
BIG_AMOUNT = 50_000
CC_MISMATCH_WARN = 200


# ------------------------------------------------------------ shared helpers

def load_profiles() -> dict:
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_profiles(profiles: dict) -> None:
    header = (
        "# MACHINE-WRITTEN by `import_transactions.py inspect` on human confirm.\n"
        "# Do not hand-edit — sign conventions are confirmed against a real\n"
        "# export, never typed in (§2.1.5).\n"
    )
    fsio.write_text(PROFILES_PATH, header + yaml.safe_dump(profiles, sort_keys=True))


def kind_of(category: str | None) -> str:
    """Same derivation as the Notion Kind formula — the firewall, locally."""
    c = category or ""
    if c.startswith("Contribution — "):
        return "Contribution"
    if c.startswith("Income — "):
        return "Income"
    if c.startswith("Transfer — "):
        return "Transfer"
    return "Expense"


def row_hash(account_key: str, raw_date: str, raw_amount: str, raw_desc: str, dup_index: int) -> str:
    blob = f"{account_key}|{raw_date}|{raw_amount}|{raw_desc}|{dup_index}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def month_filter(month: str) -> dict:
    return {"property": "Month", "formula": {"string": {"equals": month}}}


def read_tx(page: dict) -> dict:
    return {
        "id": page["id"],
        "hash": "".join(
            t.get("plain_text", "") for t in page["properties"]["Hash"]["rich_text"]
        ),
        "description": napi.read_title(page, "Description"),
        "date": napi.read_date(page, "Date"),
        "amount": napi.read_number(page, "Amount"),
        "account": napi.read_select(page, "Account"),
        "category": napi.read_select(page, "Category"),
    }


# ------------------------------------------------------------ re-aggregation

def re_aggregate_month(client: napi.Notion, ids: dict, month: str, dry: bool = False) -> dict:
    """Fresh post-write query → Monthly Money upsert (script fields only)."""
    txs = [read_tx(p) for p in client.query_db(ids["transactions"], filter=month_filter(month))]
    income = spend = 0.0
    contrib: dict[str, float] = {"TFSA": 0.0, "RRSP": 0.0, "FHSA": 0.0, "Taxable": 0.0}
    for t in txs:
        k = kind_of(t["category"])
        amt = t["amount"] or 0.0
        if k == "Income":
            income += amt
        elif k == "Expense":
            spend -= amt  # stored positive, net of refunds
        elif k == "Contribution":
            shelter = (t["category"] or "").removeprefix("Contribution — ")
            if shelter in contrib:
                contrib[shelter] += -amt  # sign-normalized positive
    fields = {
        "Income": round(income, 2),
        "Spend": round(spend, 2),
        "Contrib TFSA": round(contrib["TFSA"], 2),
        "Contrib RRSP": round(contrib["RRSP"], 2),
        "Contrib FHSA": round(contrib["FHSA"], 2),
        "Contrib Taxable": round(contrib["Taxable"], 2),
    }
    if dry:
        print(f"  [dry] {month}: {fields} ({len(txs)} rows)")
        return fields
    existing = list(
        client.query_db(
            ids["monthly_money"],
            filter={"property": "Month", "title": {"equals": month}},
        )
    )
    if len(existing) > 1:
        raise SystemExit(
            f"Monthly Money has {len(existing)} rows titled {month!r} — refusing "
            f"to guess. Merge/delete the duplicates in Notion, then re-run."
        )
    props = {k: napi.number(v) for k, v in fields.items()}
    if existing:
        client.update_page(existing[0]["id"], props)
    else:
        props["Month"] = napi.title(month)
        props["Month Start"] = napi.date_prop(f"{month}-01")
        client.create_page(ids["monthly_money"], props)
    print(f"  re-aggregated {month}: rows={len(txs)} income={fields['Income']} spend={fields['Spend']}")
    return fields


def run_export(client: napi.Notion, ids: dict) -> None:
    rows = mm_export.month_rows(client, ids["monthly_money"])
    n = mm_export.write_export(rows, EXPORT_PATH)
    blank = len(rows) - n
    print(f"export: {n} complete month(s) → {EXPORT_PATH}" + (f" ({blank} blank-Net-Worth skipped)" if blank else ""))


# ------------------------------------------------------------------- import

def discover_drops(profiles: dict) -> list[tuple[Path, str, dict]]:
    """(file, account_key, profile) for every contract-named CSV in drops/."""
    found = []
    if not DROPS.is_dir():
        return found
    for month_dir in sorted(DROPS.iterdir()):
        if not month_dir.is_dir():
            continue
        for key, profile in profiles.items():
            p = month_dir / profile["drop_name"]
            if p.exists():
                found.append((p, key, profile))
    return found


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_resume_journal(file_sha: str) -> dict | None:
    for jp in sorted(IMPORT_STATE.glob("*.json")):
        j = fsio.read_json(jp) or {}
        if j.get("file_sha") == file_sha and j.get("phase") != "done":
            return j
    return None


def import_one(
    client: napi.Notion,
    ids: dict,
    ruleset,
    path: Path,
    key: str,
    profile: dict,
    assume_yes: bool,
) -> dict | None:
    sidecar = path.parent / f".imported-{key}.json"
    file_sha = _file_sha(path)
    prior = fsio.read_json(sidecar)
    if prior and prior.get("sha256") == file_sha:
        print(f"  {path.parent.name}/{path.name}: unchanged since batch {prior['batch_id']} — skip")
        return None

    rows = parse_file(path, key, profile)  # ParserAbort → nothing written
    account = profile["account"]

    # hashes with dup_index (byte-identical lines survive dedupe separately)
    seen: Counter = Counter()
    hashed = []
    for r in rows:
        dup = seen[r.raw_line]
        seen[r.raw_line] += 1
        hashed.append((row_hash(key, r.raw_date, r.raw_amount, r.raw_description, dup), r))

    big = [r for _, r in hashed if abs(r.amount) > BIG_AMOUNT]
    if big and not assume_yes:
        for r in big:
            print(f"  LARGE: {r.date} {r.description[:60]} {r.amount:+,.2f}")
        if input(f"  {len(big)} row(s) over ${BIG_AMOUNT:,} — continue? [y/N] ").lower() != "y":
            raise SystemExit("aborted by user at large-amount confirm")

    resume = _find_resume_journal(file_sha)
    batch_id = resume["batch_id"] if resume else f"{date.today().isoformat()}·{key}"
    journal_path = IMPORT_STATE / f"{batch_id.replace('·', '_')}.json"
    journal = resume or {
        "batch_id": batch_id,
        "file_sha": file_sha,
        "phase": "creating",
        "created": {},
    }
    fsio.write_json(journal_path, journal)

    # prefetch: per touched month ∪ journal ∪ (on resume) Import-Batch query
    months = sorted({r.date.strftime("%Y-%m") for _, r in hashed})
    existing: dict[str, dict] = {}
    for m in months:
        for page in client.query_db(ids["transactions"], filter=month_filter(m)):
            t = read_tx(page)
            if t["hash"]:
                existing[t["hash"]] = t
    if resume:
        for page in client.query_db(
            ids["transactions"],
            filter={"property": "Import Batch", "rich_text": {"equals": batch_id}},
        ):
            t = read_tx(page)
            if t["hash"]:
                existing[t["hash"]] = t

    created = skipped = updated = 0
    uncategorized = 0
    for h, r in hashed:
        iso = r.date.isoformat()
        if h in existing or h in journal["created"]:
            t = existing.get(h)
            if t:
                patch = {}
                if t["description"] != r.description:
                    patch["Description"] = napi.title(r.description)
                if t["date"] != iso:
                    patch["Date"] = napi.date_prop(iso)
                if t["amount"] != r.amount:
                    patch["Amount"] = napi.number(r.amount)
                if t["account"] != account:
                    patch["Account"] = napi.select(account)
                # NEVER Category, never Hash/Import Batch, never delete.
                if patch:
                    client.update_page(t["id"], patch)
                    updated += 1
                else:
                    skipped += 1
            else:
                skipped += 1
            continue
        category = rules_mod.categorize(r.description, r.amount, account, ruleset)
        if category == rules_mod.UNCATEGORIZED:
            uncategorized += 1
        page = client.create_page(
            ids["transactions"],
            {
                "Description": napi.title(r.description),
                "Date": napi.date_prop(iso),
                "Amount": napi.number(r.amount),
                "Account": napi.select(account),
                "Category": napi.select(category),
                "Hash": napi.rich_text(h),
                "Import Batch": napi.rich_text(batch_id),
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": r.raw_line[:1990]}}]},
                }
            ],
        )
        created += 1
        journal["created"][h] = page["id"]
        fsio.write_json(journal_path, journal)  # flushed after EVERY create ack

    cc_sum = sum(
        r.amount
        for h, r in hashed
        if rules_mod.categorize(r.description, r.amount, account, ruleset)
        == "Transfer — CC Payment"
    )

    journal["phase"] = "done"
    fsio.write_json(journal_path, journal)
    fsio.write_json(
        sidecar,
        {"sha256": file_sha, "batch_id": batch_id, "imported_at": datetime.now().isoformat(timespec="seconds")},
    )
    print(
        f"  {path.parent.name}/{path.name} [{batch_id}]: created={created} "
        f"skipped={skipped} updated={updated} uncategorized={uncategorized}"
    )
    return {"months": months, "cc_sum": cc_sum, "created": created}


def cmd_import(args) -> int:
    config = cfg.load()
    ids = config["notion"]["db_ids"]
    _, ruleset = rules_mod.load_rules(CATEGORIES_PATH)
    profiles = load_profiles()
    drops = discover_drops(profiles)
    if not drops:
        print(f"no contract-named CSVs found under {DROPS}/YYYY-MM/ — nothing to do")
        return 0
    IMPORT_STATE.mkdir(parents=True, exist_ok=True)
    client = napi.Notion()
    touched: set[str] = set()
    cc_total = 0.0
    aborted: list[str] = []
    for path, key, profile in drops:
        try:
            result = import_one(client, ids, ruleset, path, key, profile, args.yes)
        except ParserAbort as exc:
            # The FILE is the abort unit — nothing from it lands, but other
            # files' rows still deserve their re-aggregation below.
            print(f"\nABORTED (whole file, nothing written): {exc}")
            aborted.append(path.name)
            continue
        if result:
            touched.update(result["months"])
            cc_total += result["cc_sum"]
    for m in sorted(touched):
        re_aggregate_month(client, ids, m)
    if touched:
        run_export(client, ids)
    if abs(cc_total) > CC_MISMATCH_WARN:
        print(
            f"  WARNING: CC-payment rows across files sum to {cc_total:+,.2f} "
            f"(>|${CC_MISMATCH_WARN}|) — card and chequing sides may not both "
            f"be in this import window. Transfers still net out of aggregates."
        )
    if aborted:
        print(f"import finished WITH ABORTED FILE(S): {', '.join(aborted)} — fix and re-run.")
        return 1
    print("import complete.")
    return 0


# ------------------------------------------------------------------ inspect

def _infer_date_format(samples: list[str]) -> str | None:
    from datetime import datetime as dt

    candidates = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"]
    viable = []
    for fmt in candidates:
        try:
            parsed = [dt.strptime(s.strip(), fmt) for s in samples]
        except ValueError:
            continue
        viable.append((fmt, parsed))
    if not viable:
        return None
    if len(viable) > 1:
        # Disambiguate m/d vs d/m only when some component exceeds 12.
        for fmt, _ in viable:
            if fmt == "%m/%d/%Y":
                return fmt  # stated assumption; the human confirms by eye
    return viable[0][0]


def cmd_inspect(args) -> int:
    path = Path(args.file)
    profiles = load_profiles()
    if args.account not in profiles:
        raise SystemExit(f"unknown account key {args.account!r} — use one of {sorted(profiles)}")
    shape, fingerprint = compute_fingerprint(path)
    from parsers import _read_lines, _split  # noqa: PLC0415

    lines = _read_lines(path)
    body = lines[1:] if shape in ("rbc", "scotia-5col", "scotia-7col") else lines
    print(f"file:        {path}")
    print(f"shape:       {shape}")
    print(f"fingerprint: {fingerprint}")
    print(f"rows:        {len(body)}")
    print("samples:")
    for line in body[:5]:
        print(f"  {line[:110]}")
    cols = [_split(ln) for ln in body]
    acct_type = None
    if shape == "rbc":
        acct_types = sorted({c[0].strip() for c in cols if c})
        print(f"Account Type values: {acct_types}")
        if len(acct_types) != 1:
            raise SystemExit(f"mixed Account Type values {acct_types} — split the export per account")
        acct_type = acct_types[0]
    date_idx = {"rbc": 2, "scotia-3col": 0, "scotia-5col": 0, "scotia-7col": 1}[shape]
    dates = [c[date_idx] for c in cols[:20] if len(c) > date_idx]
    fmt = _infer_date_format(dates)
    if fmt is None:
        raise SystemExit(
            "could not infer a date format from the sample rows — is this "
            "file what you think it is?"
        )
    print(f"inferred date format: {fmt}  (verify against the samples above)")

    # Preview through the REAL parser at multiplier 1 — preview and import
    # share one code path, so they can never disagree again.
    trial = {
        "confirmed": True, "shape": shape, "fingerprint": fingerprint,
        "date_format": fmt, "sign_multiplier": 1, "account_type": acct_type,
    }
    parsed = parse_file(path, args.account, trial)
    print("\nrows exactly as the importer would store them:")
    for r in parsed[:5]:
        print(f"  {r.date}  {r.amount:>+12,.2f}  {r.description[:60]}")
    hi = max(parsed, key=lambda r: r.amount)
    lo = min(parsed, key=lambda r: r.amount)
    print(f"  largest inflow : {hi.date}  {hi.amount:>+12,.2f}  {hi.description[:60]}")
    print(f"  largest outflow: {lo.date}  {lo.amount:>+12,.2f}  {lo.description[:60]}")
    print(
        "\nSign check — the pipeline stores inflow + (deposits, payments "
        "received) and outflow − (purchases). Judge the rows ABOVE, as shown."
    )
    ans = input("Are the signs above correct as shown? [y/n] ").strip().lower()
    sign = 1 if ans == "y" else -1
    print(
        f"\nProposed profile for {args.account!r}: shape={shape} "
        f"date_format={fmt} sign_multiplier={sign} account_type={acct_type}"
    )
    if input("Write this profile as CONFIRMED? [y/n] ").strip().lower() != "y":
        print("not written.")
        return 1
    profiles[args.account].update(
        {
            "shape": shape,
            "fingerprint": fingerprint,
            "date_format": fmt,
            "sign_multiplier": sign,
            "account_type": acct_type,
            "confirmed": True,
        }
    )
    save_profiles(profiles)
    print(f"profile written to {PROFILES_PATH} — commit it.")
    return 0


# -------------------------------------------------------------- recategorize

def cmd_recategorize(_args) -> int:
    config = cfg.load()
    ids = config["notion"]["db_ids"]
    _, ruleset = rules_mod.load_rules(CATEGORIES_PATH)
    client = napi.Notion()
    touched: set[str] = set()
    moved = 0
    for page in client.query_db(
        ids["transactions"],
        filter={"property": "Category", "select": {"equals": rules_mod.UNCATEGORIZED}},
    ):
        t = read_tx(page)
        new = rules_mod.categorize(t["description"], t["amount"] or 0.0, t["account"] or "", ruleset)
        if new != rules_mod.UNCATEGORIZED:
            client.update_page(t["id"], {"Category": napi.select(new)})
            moved += 1
            if t["date"]:
                touched.add(t["date"][:7])
    print(f"recategorize: {moved} row(s) left Uncategorized → rules")
    for m in sorted(touched):
        re_aggregate_month(client, ids, m)
    if touched:
        run_export(client, ids)
    return 0


# -------------------------------------------------------------- repair-batch

def cmd_repair_batch(args) -> int:
    config = cfg.load()
    ids = config["notion"]["db_ids"]
    client = napi.Notion()
    pages = list(
        client.query_db(
            ids["transactions"],
            filter={"property": "Import Batch", "rich_text": {"equals": args.batch_id}},
        )
    )
    if not pages:
        print(f"no rows carry Import Batch {args.batch_id!r}")
        return 1
    months = set()
    for p in pages:
        t = read_tx(p)
        if t["date"]:
            months.add(t["date"][:7])
        print(f"  {t['date']}  {t['amount']:>12,.2f}  {t['category'] or '—':<24} {t['description'][:50]}")
    print(f"{len(pages)} row(s) in batch {args.batch_id}")
    if not args.delete:
        return 0
    if not args.yes and input(
        f"Archive all {len(pages)} rows to Notion trash (30-day recoverable)? [y/n] "
    ).lower() != "y":
        return 1
    for p in pages:
        client.request("PATCH", f"/pages/{p['id']}", {"archived": True})
    for sidecar in DROPS.glob("*/.imported-*.json"):
        if (fsio.read_json(sidecar) or {}).get("batch_id") == args.batch_id:
            sidecar.unlink()
            print(f"  dropped sidecar {sidecar}")
    jp = IMPORT_STATE / f"{args.batch_id.replace('·', '_')}.json"
    jp.unlink(missing_ok=True)
    for m in sorted(months):
        re_aggregate_month(client, ids, m)
    run_export(client, ids)
    print(f"batch {args.batch_id} archived; months re-aggregated.")
    return 0


# --------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description="Money pipeline")
    sub = parser.add_subparsers(dest="cmd")
    p_imp = sub.add_parser("import")
    p_imp.add_argument("--yes", action="store_true", help="skip the >$50k interactive confirm")
    p_ins = sub.add_parser("inspect")
    p_ins.add_argument("file")
    p_ins.add_argument("--account", required=True)
    p_re = sub.add_parser("re-aggregate")
    p_re.add_argument("month", metavar="YYYY-MM")
    sub.add_parser("export")
    sub.add_parser("recategorize")
    p_rb = sub.add_parser("repair-batch")
    p_rb.add_argument("batch_id")
    p_rb.add_argument("--list", action="store_true")
    p_rb.add_argument("--delete", action="store_true")
    p_rb.add_argument("--yes", action="store_true", help="skip the archive confirm")
    args = parser.parse_args()

    cmd = args.cmd or "import"
    if cmd == "import":
        if not hasattr(args, "yes"):
            args.yes = False
        return cmd_import(args)
    if cmd == "inspect":
        return cmd_inspect(args)
    if cmd == "re-aggregate":
        config = cfg.load()
        client = napi.Notion()
        re_aggregate_month(client, config["notion"]["db_ids"], args.month)
        run_export(client, config["notion"]["db_ids"])
        return 0
    if cmd == "export":
        config = cfg.load()
        run_export(napi.Notion(), config["notion"]["db_ids"])
        return 0
    if cmd == "recategorize":
        return cmd_recategorize(args)
    if cmd == "repair-batch":
        return cmd_repair_batch(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
