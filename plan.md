# Notion Life OS v1 — Build Plan

Phase 3 of `notion-os-spec.md`. **Pure ordering — no new design**: every checkbox traces to §1 (schema, incl. §1.12) or §2 (sync architecture, incl. §2.8). Nine sessions: Friday evening leaves the social CRM live before any code exists; Saturday/Sunday build the pipelines; the iOS Shortcut and Excel workbook spill into two short weeknights, with the launchd install deliberately **last** (it gates on a human-confirmed test notification and effect asserts, §2.1.7).

**Labels** — every step carries exactly one:
`[hand · Notion UI]` · `[hand · terminal]` · `[hand · bank/phone]` · `[build]` (code written in-session) · `[verify]` (on-device or against-real-data check)

**Timing** (honest bands, ceilings not targets): Fri ~3–3.5h · Sat ~7–8h · Sun ~7.5–9h · two weeknights ~1.5h + ~2–3h. Shed-load valves if a day runs long: Session 1's Directory/Needs Tier views and the Goals page can trail without breaking its acceptance; Session 7 can slide to a weeknight (the dead-man isn't needed until the first Friday after the sitting).

**Standing invariants** (§2.6 — bind every build step): Hash + Import Batch ride in the one create call; Category is written once and never again by any script path except `recategorize`-on-Uncategorized; Bal ×5/Liabilities are never script-written; aggregates always come from post-write Notion queries; every pipeline fails loudly or not at all.

Already done before this plan (2026-08-19, spec header): zombie Fastify kill; Garmin re-auth + 88-day gap backfill (vault continuous 2025-01-03 →).

---

## Session 1 — Notion foundation: the social CRM goes live (Fri evening, ~3–3.5h)

**Goal:** all five databases with every §1.1 property and formula, all 12 §1.3 views, the Touch template, both integrations, seed data — Due view + manual capture work end-to-end with zero code.

- [ ] `[hand · Notion UI]` Create **People** DB with Name (title), Tier (select — options exactly `A`/`B`/`C`, cadence legend in the property *description*, no parentheticals in option names), Cadence Override (number), Effective Cadence (formula — 14/30/90 by tier, override wins, 60-day fallback). *Days Since and Due come later — their inputs don't exist yet.* (§1.1.3)
- [ ] `[hand · Notion UI]` Create **Interactions** DB: Name (title, optional), Date (date), People (relation → People, multi-page, dual property "Interactions"), Type (select: `1:1` default, `Group`, `Call`, `Async`). Exactly four properties — nothing else, protecting the <10s budget. (§1.1.2)
- [ ] `[hand · Notion UI]` Add **People.Last Contact** — rollup: relation Interactions, target Date, aggregation **Latest date**. The system's only rollup; UI-render-only, never API-read. (§1.1.3, §1.10)
- [ ] `[hand · Notion UI]` Now add **People.Days Since** (formula: 9999 sentinel on empty Last Contact) and **People.Due** (formula: Days Since ≥ Effective Cadence) — both reference the rollup that now exists. (§1.1.3)
- [ ] `[hand · Notion UI]` Create **Weekly Log** DB: Week (title), Week Start (date), Month Key (formula `formatDate` YYYY-MM), Weight Avg, Weight Delta, Training Sessions, Training Load, PT Sessions, Sleep Avg, Sleep Score, RHR, HRV, Social Touches, Days With Data (all number). Zero relations, zero rollups. (§1.1.1)
- [ ] `[hand · Notion UI]` Create **Transactions** DB: Description (title), Date, Amount (number, signed CAD), Account (select: RBC Chequing / RBC CC / Scotia Visa), Category (select — full taxonomy incl. **Phone**: plain spend names + `Income — *` + `Contribution — TFSA/RRSP/FHSA/Taxable` + `Transfer — CC Payment/Internal` + Uncategorized), Kind (formula from Category prefixes — the double-counting firewall), Month (formula YYYY-MM), Hash (rich_text), Import Batch (rich_text). No relations. (§1.1.4, §2.8.4)
- [ ] `[hand · Notion UI]` Create **Monthly Money** DB: Month (title YYYY-MM), Month Start (date), Income, Spend, Contrib TFSA/RRSP/FHSA/Taxable, Bal Chequing/TFSA/RRSP/FHSA/Taxable, Liabilities (all number), Surplus (formula), Savings Rate (formula), **Net Worth** (the guarded completeness formula — THE one authoritative number; blank until all six hand-entered cells exist). (§1.1.5)
- [ ] `[hand · Notion UI]` Create the **"Touch" template** on Interactions — Date = dynamic @Today, Type = 1:1 — set as default template for all views; capture sheet shows exactly Date / People / Type. (§1.3)
- [ ] `[hand · Notion UI]` People views: **Due** (default — filter Due checked, sort Days Since desc, page-load limit 10), **Directory**, **Needs Tier** (filter Tier empty). (§1.3)
- [ ] `[hand · Notion UI]` Interactions view: **Recent** (default, Date desc). (§1.3)
- [ ] `[hand · Notion UI]` Weekly Log views: **Timeline** (default — Week Start desc; column calcs: averages on Weight/Sleep/Score/RHR/HRV, sums on Load/Sessions/Touches) and **By Month** (group by Month Key desc, same calcs). (§1.3)
- [ ] `[hand · Notion UI]` Transactions views: **By Month** (default — group Month desc, filter Kind ≠ Transfer, per-group Sum), **Last 30 Days by Category** (Kind = Expense, rolling 30d, group Category), **Uncategorized** (the maintenance queue), **Contributions** (Kind = Contribution, group Category). (§1.3)
- [ ] `[hand · Notion UI]` Monthly Money views: **Ledger** (default, Month desc, all columns — blank Net Worth is the built-in nag) and **Export** (Month asc, exactly the 16 export columns in CSV order). (§1.3)
- [ ] `[hand · Notion UI]` Create both integrations at notion.so/my-integrations: **notion-os-mac** shared to all 5 DBs; **notion-os-capture** shared ONLY to Interactions + People. Hold the tokens for Sessions 2 and 8. (§2.3)
- [ ] `[hand · Notion UI]` Enter ~30 **People** with Tiers (Cadence Override only where genuinely wanted). (§1.1.3, §1.11)
- [ ] `[hand · Notion UI]` Enter ~30 **backdated seed Interactions** (one per person, rough real last-contact dates) — Due opens as a ranked list, not a 30-person 9999 wall. (§1.6, §1.8)
- [ ] `[hand · Notion UI]` Create the static **2026 Goals** page, pinned at the workspace top (the v1 goals surface — no Goals DB). (§1.7.6)
- [ ] `[hand · bank/phone]` Pin the Notion widget showing the People **Due** view to the iOS home screen. (§1.3)
- [ ] `[verify]` On the actual phone: capture one real Touch via widget → + New → template (@Today and 1:1 must apply on-device; type 2–3 letters, pick the person, swipe away). This is the *pre-check*; formal timing of both paths happens in Session 8. (§1.4)
- [ ] `[hand · bank/phone]` **ORDER THE SMART SCALE NOW** — Garmin Index-family, or any scale with a maintained Garmin Connect bridge (weigh-ins must land in Garmin Connect). Shipping lead time is why this is a Session-1 line. (§1.12.1)

**Works after this session:** the social CRM, end-to-end, zero code — Due shows a ranked ≤10-row list on the widget; a phone capture updates Last Contact and clears the person from Due; all 12 views render; both tokens exist; the scale is ordered.

---

## Session 2 — Repo scaffold, secrets closed, vault sync revived (Sat morning, ~2h)

**Goal:** monorepo skeleton; every §0.10 secret exposure closed; the `_sync` three-commit weight delta pushed and verified.

- [x] `[hand · terminal]` Scaffold `~/notion-os` per the ratified tree: `config/ scripts/ money/ lib/ launchd/ state/ drops/ exports/ logs/`; gitignore `state/ drops/ exports/ logs/ .venv/`; create `.venv` with requests, PyYAML, python-dotenv. (§2.3) *Done 2026-08-24.*
- [x] `[hand · terminal]` Secrets relocation: `mkdir -m 700 ~/.config/notion-os`; move `Vault/Garmin/_sync/.env` → `~/.config/notion-os/garmin.env` (600), delete the vault copy; create `notion.env` (600) with the notion-os-mac token. The capture token never lives in a file — Shortcut only, Session 8. (§2.3, §0.10) *Done 2026-08-24 — except `notion.env` is a stub: paste the notion-os-mac token after Session 1 creates it.*
- [ ] `[hand · terminal]` Delete the expired Google `credentials.json` and `token.json` from `~/Downloads/mission-control/scripts/`. (§2.3, §0.10) *Human-only: automated delete was blocked by tooling permissions.*
- [x] `[build]` `_sync` commit 1: `extractors.py` + `body_comp_fields` (~25 lines, existing `_num/_round/_in_range` idioms, `WEIGHT_KG_RANGE=(30.0,250.0)`); `discovery.py` + the body-comp probe. (§2.1.1) *c70746c.*
- [x] `[build]` `_sync` commit 2: `sync.py` + the body-composition fetch entry (calendar-day metric, no D+1 shift) + one `fm.update` line. (§2.1.1) *37cf640.*
- [x] `[build]` `_sync` commit 3: `auth_test.py` dotenv path → `~/.config/notion-os/garmin.env`. (§2.1.1) *dd96543 — also repointed the stale `.env` mentions in both error messages; the "Authentication failed" classifier substring is untouched.*
- [x] `[hand · terminal]` Push the three commits to the `_sync` GitHub remote. Untouched by design: `garmin_io.fetch` (new endpoint inherits the whole 429/retry/404 policy), `notes.py` body preservation, `state.py`, `GAP_FILL_LOOKBACK=2`. (§2.1.1, §2.4) *Pushed 2026-08-24.*
- [x] `[verify]` Run `sync.py` by hand from the relocated env against the real vault: fresh login works, today's note written with body preserved, weight columns blank on an empty body-comp payload (`{}` by construction — garbage can never be written). (§2.1.1) *6/6 days 08-19→08-24, 0 warnings; zero weight keys in any note; body preserved. NOTE: the watch itself has landed no data since 2026-06-28 — recent notes are `{date, source}` only. Wear/sync the watch or Weekly Log's recent weeks will honestly read Days With Data = 0.*
- [x] `[build]` `config/config.yml` (committed, non-secret): the 5 DB ids from Session 1, vault/`_sync`/Shortcuts-container paths, pinned Notion-Version, `pt_type_allowlist: [strength_training]`, `deadman_window_months: 12`, `export_horizon_warn_d: 300`, `system_start_month: null` (set at the first sitting, Session 6 — the dead-man's cold-start floor), notification thresholds, per-account parser profile stubs (fingerprint/sign unconfirmed until `inspect`, Session 5). (§2.3, §2.8, §2.1.4) *Done — DB ids null until Session 1.*

**Works after this session:** the vault sync runs clean from relocated secrets; zero credentials remain in the vault or Downloads; config carries every §2.8 value; the weight extension is live and provably harmless while no scale data exists.

---

## Session 3 — `lib/` and the daily wrapper (Sat midday, ~2h)

**Goal:** the one shared library both workstreams depend on, then `garmin_daily.py` — the vault sync becomes unkillable-by-gap and loud-on-death.

- [ ] `[build]` `lib/` as ONE item, before both workstreams: `notion_api.py` (token bucket ≤3 req/s; 429 honors Retry-After else 1/2/4…60s max 5; 5xx/conn once; 400/401/403/404 never — immediate loud abort naming the runbook/property; write failures abort the run), `notify.py` (osascript, always mirrored to log, per-run dedupe), `weeks.py` (ISO-week math), `fsio.py` (atomic tmp+rename JSON for all new state). (§2.1.6)
- [ ] `[build]` `scripts/garmin_daily.py` (~150 lines): the one shared blocking flock around every `sync.py` invocation; freshness skip; gap chooser (≤14 → gap-fill, >14 → `--since last_sync − 2d`); auth-suspect substring classification → immediate runbook notification + `auth_dead` flag that stops the daily retry; other failures quiet ×2, notify on the 3rd (§2.8.1 grace kept); meta-watchdog over rollup + deadman state — **tolerating missing state files silently until the watched job's first successful run** (so build-weekend hand-runs never fire spurious notifications). (§2.1.2, §2.0, §2.8.1)
- [ ] `[verify]` Two consecutive hand runs: first syncs, second freshness-skips; force one failure and confirm the notification visibly appears and lands in the log. (Formal channel gate = install, Session 9.) (§2.1.2, §2.0)

**Works after this session:** one command keeps the vault current, refuses to double-run, classifies auth death immediately, and is loud on failure.

---

## Session 4 — `weekly_rollup.py` and the 85-week backfill (Sat afternoon, ~3–4h)

**Goal:** the health spine works end-to-end by hand; Weekly Log carries the full history.

- [ ] `[build]` `scripts/weekly_rollup.py` (~470 lines), steps 0–7 exactly per §2.1.3: lock + freshen (flag-and-continue on sync failure); target weeks (trailing-4 ∪ missed, cap 12, in-progress week never written); pure-local aggregation (Days With Data = notes with ≥1 metric key beyond `{date, source}`; sleep coalesce per Years.md; Weight Delta walks back to the prior non-blank week); Interactions self-heal *before* counting; offline replay from `pending/<uuid>.json` (uuid-in-body dedupe, delete-on-success, dead-letter after 3); Social Touches via one date-range query; full-row trailing-window upsert with explicit nulls; people-cache export; finally-block watchdog. Every step idempotent. (§2.1.3, §0.11)
- [ ] `[verify]` `--dry-run` against the real vault + real Notion: aggregates sane, non-uniform frontmatter tolerated. (§2.1.3, §0.11)
- [ ] `[hand · terminal]` First live run: trailing weeks land; Session-1 seed Interactions appear in Social Touches; Timeline calcs populate. (§2.1.3)
- [ ] `[hand · terminal]` `--backfill 2025-W01` — the one-time ~85-row backfill (local aggregation, throttled creates, ~30–60s, rerunnable). (§2.1.3, §1.6)
- [ ] `[verify]` Spot-check: ~85 continuous rows 2025-W01 → current, zero missing weeks; PT Sessions honestly 0 throughout; Weight columns blank — not 0; By Month averages sensible. (§1.1.1, §1.12)
- [ ] `[verify]` `notion-people.json` exists in the Shortcuts iCloud folder, tier-sorted — the Mac side of the container contract, pre-verified ahead of Session 8. (§2.1.3, §2.1.8)

**Works after this session:** the entire health half — ~85 weeks of history plus self-updating trailing weeks; only the scheduler (Session 9) is pending, by design.

---

## Session 5 — Real bank CSVs, then the parsers (Sun morning, ~2.5–3h)

**Goal:** real CSVs on disk first (none exist anywhere), then parsers and rules fingerprint-confirmed against them — before a single Notion write.

- [ ] `[hand · bank/phone]` Export real CSVs: RBC Chequing + RBC CC from RBC online banking; Scotia Visa direct CSV (§2.8.2 — no PDF step). Save into `drops/YYYY-MM/` under the contract names `rbc-chequing.csv` / `rbc-cc.csv` / `scotia-visa.csv` — the rename IS the account+month binding. (§2.1.5)
- [ ] `[build]` `money/parsers.py`: RBC family parser (8-column header verified against the old xlsx, Account Type cross-check); Scotia Visa both candidate shapes (`inspect` arbitrates); fingerprint re-check before row 1; whole-file abort before any Notion write on drift / >2% unparseable / USD$ populated / account mismatch; `parseAmount`+BOM+local-date lessons ported from lighthouse; `bank.js`'s three silent-misparse vectors explicitly not ported. (§2.1.5, §2.4)
- [ ] `[build]` `money/rules.py` + `config/categories.yml`: ordered first-match-wins rules with account/sign/amount guards; 63-rule seed remapped to the §1.1.4 taxonomy; `E-TRANSFER IN` ordered **above** `TRANSFER`; loader hard-fails on unknown categories; no match → Uncategorized, never a guess. (§2.1.5, §1.12.3)
- [ ] `[build]` The loader unit fixture proving the shadow-rule check against the real seed (the e-transfer ordering pair). (§2.1.5, §2.6)
- [ ] `[hand · terminal]` The ~5-minute `categories.yml` review, then commit: Cineplex/Ticketmaster → Misc; SHAW/TELUS/ROGERS → **Phone**; contribution rules watch RBC Direct Investing / InvestEase descriptors; Shoppers/London Drugs → Health (seed default — the one §2.8.4 sub-answer still open, decide here). (§2.8.4)
- [ ] `[build]` The `inspect` subcommand: prints header/columns/samples/inferred sign (showing a known payroll or purchase row); on human confirm writes `{fingerprint, date_format, sign_multiplier, confirmed}` into config. *If time allows, start the import internals' network-free layers (parse → hash → journal) here — they need no Notion writes, so this session's acceptance still holds.* (§2.1.5)
- [ ] `[verify]` Run `inspect` on all three real exports and confirm each format and sign by eye — the RBC-CC purchase sign is the single most import-breaking unknown; confirmed here, never guessed. (§2.1.5)

**Works after this session:** all three real formats fingerprint-confirmed with human-verified signs in config; the rules loader passes its fixture; not one Notion write has happened yet.

---

## Session 6 — The money pipeline and the first sitting (Sun afternoon, ~3.5–4.5h)

**Goal:** the import machinery, the first real import, the first sitting — Monthly Money ends the session with THE authoritative Net Worth non-blank.

- [ ] `[build]` `import_transactions.py` import internals per §2.1.5: pure parse → hash with dup_index → journal `state/import/<batch-id>.json` → prefetch (paginated Month-equals ∪ journal ∪ on-resume Import-Batch query) → creates carrying ALL properties incl. Hash + Import Batch in the one call + verbatim raw line as children; updates touch script-owned fields only, never Category, never delete; **journal flushed after every create ack, never before** → re-aggregate each touched month from a fresh post-write query → Monthly Money upsert (script-owned fields only) → gated export → sidecars → summary printout (counts, Uncategorized, per-month Income/Spend, CC-payment mismatch warning, >$50k interactive confirm). Resume-safe at every step. (§2.1.5, §2.6)
- [ ] `[build]` Subcommands `re-aggregate` · `export` · `recategorize` (touches only currently-Uncategorized rows, then auto-re-aggregates). *`repair-batch` moves to Session 7 — it's only needed after a bad import.* (§2.1.5)
- [ ] `[hand · terminal]` **First real import.** Read the whole summary. (§2.1.5)
- [ ] `[verify]` Against-real-data pass: By Month totals plausible; Transfer rows (CC payments in both CSVs) net to zero everywhere; **re-run the identical import → all skips** (idempotency proven on real rows); byte-identical duplicate lines landed separately via dup_index. (§1.1.4, §2.1.5)
- [ ] `[hand · Notion UI]` Work the first Uncategorized queue: fix the obvious rows in the view. (§1.3, §1.1.4)
- [ ] `[hand · terminal]` Promote recurring merchants into `categories.yml`; run `recategorize` (auto-re-aggregates); confirm Kind flips instantly with each Category fix. (§2.1.5)
- [ ] `[hand · terminal]` Set `system_start_month` in `config.yml` to this first statement month — the dead-man's cold-start floor (months before the system existed can never nag). (§2.1.4)
- [ ] `[hand · bank/phone]` Read the six ground-truth numbers from statements: Bal Chequing/TFSA/RRSP/FHSA/Taxable (all five from RBC, §2.8.4) + Liabilities. Two portals total: RBC + Scotia. (§1.1.5)
- [ ] `[hand · Notion UI]` Type the five balances + Liabilities into the month's row — Liabilities as an explicit 0 if none (empty blocks Net Worth by design). Net Worth appears. (§1.1.5)
- [ ] `[hand · terminal]` `import_transactions.py export` — the gated export emits the completed month into `exports/monthly_money.csv` (16 columns, Month asc). (§1.5)
- [ ] `[verify]` **THE number**: Net Worth non-blank, equals the arithmetic of the six typed cells, matched by the export CSV, computed nowhere else. (§1.1.5, §1.5, §1.10)

**Works after this session:** first money import done the same weekend; one complete Monthly Money row with the authoritative Net Worth; provable idempotency; the ~15-minute sitting performed once, end to end.

---

## Session 7 — Dead-man switch, repair tooling, runbooks (Sun evening or weeknight, ~1.5–2h)

**Goal:** the single dead-man switch verified quiet-when-complete; the repair path exists; every failure notification points at a written runbook.

- [ ] `[build]` `scripts/deadman_check.py` (~140 lines): one paginated Monthly Money query over the trailing 12-month window **floored at `system_start_month`**; pending = any window month (excl. current) missing or blank-Net-Worth; ONE notification naming all pending months + empty balance columns, urgent wording near `export_horizon_warn_d = 300`; max one notification/week, no stacking; export regen on stamp-map change (full atomic rewrite); stale import-journal check (>1h); its own failure notifies louder than the nag it replaces. (§2.1.4, §2.8.3)
- [ ] `[build]` `repair-batch <id> --list/--delete` (moved from Session 6): archive a bad batch to Notion trash (30-day recoverable), drop the sidecar, auto-re-aggregate. (§2.1.5)
- [ ] `[verify]` Hand-run against real state: with the sitting done and the floor set, correct **no-nag** behavior; a stamp change (e.g. after `recategorize`) triggers a full export regen; the once-per-week cap holds across a second run. (§2.1.4)
- [ ] `[build]` README: copy the seven §2.5 runbooks verbatim — Garmin token death; Notion token rotation; CSV format drift; machine off a month; Shortcut field failure; bad-import repair; the monthly sitting itself. (§2.5)

**Works after this session:** the money nag exists and is provably quiet when the ledger is complete; every notification's instruction has a written destination.

---

## Session 8 — iOS Shortcut "Touch" (weeknight 1, ~1–1.5h)

**Goal:** the primary capture path — sub-5-second lock-screen capture — with the two verify-first risks retired or their committed fallbacks engaged.

- [ ] `[build]` Build the Shortcut on-device per the §2.1.8 data contract: read `notion-people.json` (locally cached — menu works offline) → Choose from List (tier-A first, trailing "Options…" submenu for Group/Call/Async) → POST `/v1/pages` with the **capture token** (pasted into the Shortcut's Text action — its only home): People + Type + Date = now, title omitted, `capture-uuid` children paragraph; offline/non-200 → `pending/<uuid>.json` + "Saved offline — syncs Monday"; bind to Action Button / lock screen. (§2.1.8, §2.3)
- [ ] `[verify]` Verify-first #1 — **title-omitted create** lands and shows in Recent (healed to `MMM D · Type` next Monday). Committed fallback stands if the API refuses. (§2.1.8)
- [ ] `[verify]` Verify-first #2 — **Shortcuts-container readability under launchd**, best-effort here: optionally spawn the rollup's cache/replay steps via a throwaway one-shot `launchctl` job; otherwise the **formal gate is Session 9's install.sh effect-assert** (notion-people.json written in the container by a real launchd job). Committed fallback: the manually-pasted dictionary menu. (§2.1.8, §2.1.7)
- [ ] `[verify]` **Measure both capture paths on the actual phone, from lock screen including app launch** (the honest accounting): Shortcut ~3–5s, app path ~8–10s warm. Then the offline branch: airplane mode → pending file + message; hand-run `weekly_rollup.py` → replay, uuid-dedupe, file deleted. (§1.4, §2.1.3)

**Works after this session:** sub-5-second capture from the lock screen through the money-blind capture token; offline capture provably queues, replays, and dedupes.

---

## Session 9 — Excel workbook + launchd install: the system goes autonomous (weeknight 2, ~2–3h)

**Goal:** the one-way Excel boundary, then the three plists + `install.sh` — deliberately last, gated on the human-confirmed notification and effect asserts.

- [ ] `[build]` The **Excel projection workbook** — a new build (§0.9.1): seed sheet structure from Personal_Cash_Flow_2026.xlsx's FIRE / BC Tax / Assumptions; delete its Transactions and Budget-vs-Actual sheets; t=0 = latest complete row's Net Worth + per-account balances; run-rate inputs = trailing-12-month means referencing `exports/monthly_money.csv`, never hand-typed. Strictly one-way; no write-back, ever. (§1.5, §1.7.11)
- [ ] `[verify]` Open against the real export: t=0 matches Notion's Net Worth exactly; the fixed-path external reference resolves. (§1.5)
- [ ] `[build]` `launchd/`: the three plists — garmin-daily (daily 07:15), weekly-rollup (Mon 07:40), deadman (Fri 09:00) — all RunAtLoad=true (debounce lives in the scripts; run-on-wake fits the usually-asleep Mac, §2.8.5), logs → `~/Library/Logs/notion-os/`. (§2.1.7)
- [ ] `[build]` `launchd/install.sh`: `doctor.py` preflight → **test notification with human y/n gate before bootstrapping anything** → copy plists → bootstrap + kickstart → **assert effects, not exit codes** (daily-note mtime advanced; notion-people.json in the container; deadman state stamped), failures naming the Full Disk Access fix; `--doctor` re-runs asserts + rotates logs. (§2.1.7)
- [ ] `[hand · terminal]` Run `install.sh`; confirm the test notification by eye at the gate. (§2.1.7)
- [ ] `[verify]` `--doctor` passes all three effect asserts; job logs appear in `~/Library/Logs/notion-os/`; watchdog topology fully symmetric — no silent-death corner. (§2.0)
- [ ] `[hand · terminal]` Commit and push `~/notion-os` with this plan checked off. From this moment the recurring human obligations are exactly two: the <10s capture and the ~15-minute monthly sitting. (§2.0, §1.10)

**Works after this session:** v1 is autonomous — it survives total neglect and fails loudly or not at all.

---

## When the scale arrives

- [ ] `[hand · bank/phone]` Pair the scale so weigh-ins land in **Garmin Connect**; take a first weigh-in. (§1.12.1)
- [ ] `[hand · terminal]` Run the `discovery.py` body-comp probe against the weigh-in day — the gate before trusting field names. (§2.1.1)
- [ ] `[build]` Adjust `body_comp_fields` if the probe shows different names/units (existing idioms, `WEIGHT_KG_RANGE`). (§2.1.1)
- [ ] `[verify]` Next daily sync: `weight_kg` in that day's frontmatter, in range — blank on any mismatch, never garbage. (§2.1.1)
- [ ] `[verify]` Next Monday rollup: Weight Avg populates; Weight Delta stays blank — never 0 — until a second non-blank week exists. (§1.1.1)

## Deferred (v2) — carried from §1.9, untouched

Commitments DB (ships with its first agent writer) · Goals/KR DB (gated on a review cadence surviving 8+ weeks) · initiated-by as Me/Them/Mutual + reciprocity · Balances/Accounts snapshot rows · CSV-derived balance prefill · LLM-assisted categorization · split transactions & cash itemization · materialized Category×Month table · contribution-room tracking · weekly money pulse · live bank sync (only if the ritual fails twice despite the dead-man) · email/calendar integration (blocked on OAuth Testing-mode anyway) · Obsidian journal bootstrap · daily-granularity health data / extra Garmin aggregates / dashboard rebuilds · notifications beyond the two watchdogs · rent-vs-own tab · net-worth trend columns · Interactions By-Week view.

## Definition of done (v1)

- [ ] ~85 weeks of health history in Weekly Log, zero missing weeks, current week arriving automatically every Monday. (§1.11)
- [ ] A seeded, capped Due view pinned as the home-screen widget, correct under total neglect. (§1.3)
- [ ] Sub-5-second capture measured on the actual phone; proven offline queue; app path as fallback. (§1.4)
- [ ] First money import done; Transactions idempotent on re-run; Monthly Money's guarded Net Worth non-blank — THE one authoritative number. (§1.1.5)
- [ ] `exports/monthly_money.csv` feeding the new projection workbook strictly one-way, t=0 matching Notion. (§1.5)
- [ ] All three launchd jobs installed behind the human-confirmed notification channel, effect asserts green, watchdog topology symmetric. (§2.1.7)
- [ ] All seven runbooks in the README. (§2.5)
- [ ] Secrets closed: `~/.config/notion-os/` only; vault `.env` gone; mission-control credentials deleted; capture token only in the Shortcut. (§2.3)
- [ ] Recurring human obligations are exactly two — everything else runs itself and fails loudly or not at all. (§2.0)
