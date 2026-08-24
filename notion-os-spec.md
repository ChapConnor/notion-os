# Notion Life OS v2 — Spec

**Status: Phase 2 complete — awaiting confirmation before Phase 3 (build plan).**

- Phase 0 — Inventory: complete (§0), confirmed 2026-08-19 ("go" = recommended defaults)
- Phase 1 — Schema design: complete (§1), confirmed 2026-08-19 — resolutions in §1.12
- Phase 2 — Sync architecture: **complete (§2, below)**
- Phase 3 — Build plan (`plan.md`): not started

Phase 0 → 1 housekeeping actually performed on 2026-08-19: zombie Fastify server (PID 86064) killed; Garmin re-auth + 88-day gap backfill ran clean (88/88 daily notes + 11 activity notes written; vault daily corpus now 593 notes, continuous 2025-01-03 → 2026-08-18; the ~08-22 deadline is defused). Still pending: secrets relocation (§0.10).

Method: 13 parallel agents (6 subsystem inventories, 6 independent adversarial verifiers, 1 completeness critic) swept the vault, `~/Downloads/mission-control`, `~/lighthouse`, finance spreadsheets, and every scheduler on the machine on 2026-08-19. Verdicts are based on run artifacts (logs, state files, OAuth token expiry, macOS last-used metadata), not just file mtimes. Verdict rule: ALIVE = evidence of use within ~6 weeks; DEAD = 60+ days idle, superseded, or never deployed.

---

## Phase 0 — Inventory

### 0.1 Vault identification

**Vault: `/Users/connorchapman/Documents/Obsidian/Vault`** — the only vault registered in Obsidian's `obsidian.json`, the only `.obsidian/` directory on the machine, no iCloud-synced vault, no symlinks anywhere in the path. 599 markdown files, of which 597 belong to Garmin/ and MissionControl/; the five PARA folders (`1 - Inbox` … `5 - Archive`) have been empty since vault creation (2026-03-05).

One caveat: the Obsidian Sync core plugin is enabled, so use from another device can't be 100% ruled out from local files. Locally, the vault was last opened **2026-06-13 00:22** (workspace.json) and last *written* by automation **2026-05-24 23:00**.

### 0.2 The headline

**Every subsystem is DEAD.** There is no live system to split — this project is a cold restart that can salvage good code and 16 months of Garmin history, not a migration of something running. The consistent lifecycle across all four subsystems: built in a 1–3 day burst → run manually for 0–30 days → silently abandoned when the manual trigger stopped being pressed → git-archived weeks later as a post-mortem.

Master timeline (all dates 2026):

| Date | Event |
|---|---|
| 03-05 | Vault created (Welcome.md, empty PARA folders — never used) |
| 03-16 | `personal_finance_v2.xlsx` generated; Numbers conversion abandoned same day |
| 04-13 | Mission Control built; inbox-scan ran **once, ever**; first calendar sync |
| 04-24–30 | Garmin sync built; 16 months backfilled (507 daily notes to 2025-01-03); dashboards authored |
| 04-25 | Last Mission Control calendar sync; Google OAuth token expired 17:08 that day |
| 04-25 → 05-24 | Garmin sync's entire production life (~30 days, decaying to weekly runs) |
| 05-24 23:00 | **Last write to the vault, ever** (final Garmin sync — clean, no errors) |
| 06-12/13 | Post-mortem archiving: Garmin repo pushed to GitHub, mission-control git-snapshotted, vault opened one last time |
| 07-06/07 | Lighthouse built; Fastify server started 07-07 — **still running today** (see anomalies) |
| 07-07 | `Personal_Cash_Flow_2026.xlsx` downloaded; opened once, 3 seconds later; never again |
| 07-13 | Last Lighthouse dev session (against fixture data only) |
| 08-19 15:52 | `lighthouse/.env` modified — only touch of anything in 37 days (unexplained; see anomalies) |

### 0.3 Inventory — Garmin sync (`Vault/Garmin/_sync/`)

Last actual run 2026-05-24 (87 days ago); last code edit 2026-04-27. Git history: 5 commits 04-24 → 04-27, then pushed to `github.com/ChapConnor/garmin-obsidian-sync` on 06-12 as the final touch. All items **DEAD**.

| Item | Reads | Writes | Last modified | Last run | Verdict |
|---|---|---|---|---|---|
| `sync.py` (orchestrator) | Garmin Connect API (stats, sleep D+1, HRV D+1, readiness D+1, training status, activities); `last_sync.json`; `.env` creds | `daily/*.md` (frontmatter rewritten, body preserved), `activities/*.md` (write-once), logs, `last_sync.json` | 04-27 | 05-24 23:00 | DEAD |
| `auth_test.py` (login module) | `.env`, Garmin SSO, token cache | `~/.garminconnect/garmin_tokens.json` | 04-24 | 05-24 (via sync) | DEAD |
| `extractors.py` | — (pure API-payload → frontmatter dict mapping, with validation ranges) | — | 04-24 | 05-24 (via sync) | DEAD |
| `notes.py` | existing notes (body preservation) | daily/activity markdown | 04-24 | 05-24 (via sync) | DEAD |
| `garmin_io.py` | — (API wrapper: 429 backoff 1/4/16s, retry, 404=no-data) | logs | 04-24 | 05-24 (via sync) | DEAD |
| `state.py` | `last_sync.json` | `last_sync.json` | 04-24 | 05-24 | DEAD |
| `infer_sleep.py` (HR-window sleep backfill) | daily frontmatter; minute-level HR from API | `sleep_hours_inferred` etc. into 17 daily notes | 04-25 | ~04-25 | DEAD |
| `discovery.py` / `doctor.py` (one-shot probes) | Garmin API / environment | `discovery/*.json` / stdout | 04-24 | 04-24 | DEAD |
| `last_sync.json`, `logs/` (39 files), `~/.garminconnect` tokens | — | — | 05-24 | 05-24 | DEAD |
| `daily/` — **507 notes**, 2025-01-03 → 2026-05-24, zero gaps | written by sync.py | consumed by all 5 dashboards | 05-24 | — | DEAD (data intact) |
| `activities/` — **61 notes**, 2025-01-03 → 2026-05-10 (mostly golf) | written by sync.py | consumed by dashboards | 05-11 | — | DEAD (data intact) |

Trigger chain (why it died): manual-only by explicit design (`plan.md` non-goals forbid cron). Obsidian Shell Commands "Sync Garmin" + QuickAdd macro "Sync Garmin + Refresh Date" + a Refresh button in Dashboard.md. When the button stopped being pressed after 05-24, everything stopped silently and healthily — final logs show 0 warnings.

### 0.4 Inventory — Garmin dashboards (`Vault/Garmin/*.md`)

All **DEAD** (feed frozen 05-24; vault unopened since 06-13).

| Note | Reads | Last modified | State today |
|---|---|---|---|
| `Dashboard.md` | daily + activities frontmatter, 5 dataview blocks; embeds sync button | 04-30 | Rolling `date(today)` windows → renders **empty**, looks broken |
| `Trends.md` | 30/90-day rolling windows, 4 blocks | 04-24 | Renders **empty** |
| `Weekly.md` | ISO-week grouping, LIMIT 12, 2 blocks | 04-24 | Renders, tops out at week 2026-W21 |
| `Years.md` | all-time by ISO week, 3 blocks; handles inferred-sleep asterisks | 04-25 | Renders, frozen |
| `Activities.md` | all-time activities table, 1 block | 04-24 | Renders, frozen |

### 0.5 Inventory — Mission Control (vault + `~/Downloads/mission-control/`)

Entire system live for 12 days (04-13 → 04-25) plus one note edit 04-30. OAuth token expired **2026-04-25 17:08** — the tombstone for the last authenticated API call. Git: single commit 06-12, a post-mortem snapshot. All items **DEAD**.

| Item | Reads | Writes | Last modified | Last run | Verdict |
|---|---|---|---|---|---|
| `Mission Control.md` (dashboard) | Events frontmatter via 1 dataviewjs + 3 dataview + 6 Tasks blocks | its dataviewjs **shells out** (`child_process.exec`) to run sync-calendar.js — paths to Downloads + `/opt/homebrew/bin/node` hardcoded *in the note* | 04-14 | — | DEAD |
| `daily-note-snippet.md` | Events tasks/dates | — (meant for embedding in daily notes that were never created) | 04-13 | — | DEAD |
| Templates: Deep/Quick/Recurring Prep, Weekly Review | Templater prompts | event notes (`event_title/date/time/end, location, type, status, gcal_id`; recurrence for Recurring) | 04-13 | 1 note ever created (Deep Prep → Doctor Appt Apr 29) | DEAD |
| `Data/calendar-data.md`, `calendar-synced.md` | written by sync-calendar.js | — | 04-25 16:15 | 04-25 | DEAD |
| `Data/inbox-suggestions.md` | written by inbox-scan.js | — | 04-13 | 04-13 (once, ever) | DEAD |
| `Events/` + `Events/Synced/` — 8 notes | — | — | 04-30 | — | DEAD (1 draft, 7 synced; zero ever published) |
| `inbox-scan.js` | Gmail API (readonly), `processed-emails.json`, config | `inbox-suggestions.md`, dedupe cache | 04-13 | **04-13, once** | DEAD |
| `sync-calendar.js` | GCal events.list (-2/+30 days), existing `gcal_id`s, token | `calendar-*.md`, `Events/Synced/*.md` | 04-13 | 04-25 (×2, via dashboard button) | DEAD |
| `push-to-gcal.js` (Obsidian→GCal leg) | Events with `status: publish` | GCal insert/update; writes back `gcal_id`, `published_at` | 04-13 | **never ran** — zero published notes exist | DEAD (never deployed) |
| `auth.js` / `setup-auth.js` / `config.js` | `credentials.json`, `token.json` | token refresh | 04-25 | 04-25 | DEAD |
| `cron-setup.sh` | — | would install cron (inbox 5×/day, calendar 2-hourly) | 04-13 | **never** — and would have failed: hardcodes `/usr/local/bin/node`, which doesn't exist on this Apple Silicon machine | DEAD |
| `token.json` / `processed-emails.json` / `credentials.json` | — | — | 04-25 / 04-13 / 04-13 | — | DEAD (token expired; Google "Testing" consent screen ⇒ 7-day refresh tokens ⇒ full re-auth required) |

Note: `config.js` builds the vault path portably from `$HOME`; the *hardcoding* lives in the vault dashboard note. The repo's `obsidian/` dir is the distribution source the vault copies were installed from (vault copies diverged, e.g. Mission Control.md grew 2.9KB → 13.7KB).

### 0.6 Inventory — Lighthouse / coach (`~/lighthouse/`)

**Never deployed against the real vault.** `config.json` `vault.path` is still the literal placeholder `/ABSOLUTE/PATH/TO/your-obsidian-vault`; grep finds zero references to the real vault path anywhere in the repo; every run used `vault-template/` fixtures. launchd beats never installed. Git repo has **zero commits**. All items **DEAD** except the two flagged.

| Item | Reads | Writes | Last modified | Last run | Verdict |
|---|---|---|---|---|---|
| Fastify server (`server/index.js`) | `config.json`, `data/display.json` | `coach/commitments.md` via POST /done; SSE to dashboard | 07-06 | started 07-07 19:45 | **ALIVE-as-zombie**: PID 86064, up 43 days, loopback-only (127.0.0.1:8080), serving frozen 07-13 fixture data. Never on Tailscale, never reached an iPad. |
| iPad dashboard (`dashboard/`) | GET /display + SSE | POST mark-done | 07-06 | — | DEAD (never served to a device) |
| `beat.js` (four daily beats: 06:30/12:00/18:30/22:00) | config beat times → 5 collectors → heartbeat | `data/*.json`, `display.json` | 07-06 | 07-13, manually, against fixtures | DEAD |
| `install-cron.sh` | — | would install 4 launchd plists | 07-06 | **never** (no plists, no `data/logs/`) | DEAD |
| `agent/heartbeat.js` + `assemble.js`/`rules.js`/`validate.js` | data/*.json + vault coach files via lib | `display.json`, `coach/sessions/*.md` | 07-13 | 07-13, fixtures only | DEAD |
| Agent prompts (`system/beats/weekly.md`) | — | — | 07-06 | LLM provider never activated (provider='rules'; no API key) | DEAD |
| Collectors: `weather.js` / `calendar.js` / `email.js` / `bank.js` / `cronometer.js` | Open-Meteo / ICS URL (never set) / Gmail IMAP / `drops/bank/*.csv` / `drops/cronometer/*.csv` | `data/*.json` | 07-06–13 | 07-13; **email.js never once succeeded** (no output file); bank & cronometer only ever parsed shipped sample CSVs | DEAD |
| `drops/` CSV intake (bank, cronometer) | manual CSV drops | — | 07-06 | only fixture files ever landed | DEAD (pattern relevant to our money design) |
| `vault-template/coach/commitments.md` | — | — | 07-06 | — | DEAD — **fixture with canned sample data**; see §0.9 |
| `.env` | — | — | **08-19 15:52 (today)** | no run followed | **UNKNOWN** — see anomalies |
| `config.json`, docs, `data/*.json` | — | — | 07-13 | — | DEAD (CLAUDE.md claims Phases 0–4 done incl. launchd — verifiably false) |

### 0.7 Inventory — Vault-wide sweep & plugin layer

All **DEAD**. Vault last opened 2026-06-13.

| Item | Finding | Verdict |
|---|---|---|
| `Welcome.md` | Stock starter note, verbatim default text, untouched since 03-05 | DEAD |
| `Users/connorchapman/Documents.md` | 0-byte accidental note (pasted absolute path auto-created as wikilink). Deletable with its folder chain | DEAD |
| PARA folders ×5 | Empty since creation 03-05 | DEAD |
| Core plugins | daily-notes and templates **enabled but on never-touched defaults** (no `daily-notes.json`, no `templates.json`); sync, canvas, bases, properties on | DEAD |
| Community plugins (dataview, shellcommands, tasks, templater, buttons, quickadd) | Installed in two waves (04-13, 04-29) exclusively to serve Garmin/MissionControl. Templater folder = MissionControl/Templates only. QuickAdd = exactly one macro (Sync Garmin). Buttons never saved settings | DEAD |
| Shell Commands (4: Sync Garmin, Inbox Scan, Sync Cal, Push to Cal) | None can have fired since vault last opened 06-13 | DEAD |
| `~/coding-journal` | **Not a journal** — a VS Code extension side project (interstitial journaling for devs; 5 commits 03-17 → 06-12; never installed). Its data store holds one empty crash-recovery blob | DEAD, unrelated |

### 0.8 Inventory — Finance spreadsheets & scheduling

All **DEAD** — including the one the brief calls the working model. Key evidence: all four xlsx have **birth == mtime** (each written to disk exactly once, never edited in place — generated/downloaded artifacts, not living workbooks), and macOS `mdls` last-used metadata shows none has been opened since its creation day. Zero bank CSV exports exist anywhere on the machine (home-wide search). No crontab, no finance LaunchAgents, no run logs — the scheduling layer never existed.

| File | Sheets | Created (= only write) | Last opened | Verdict |
|---|---|---|---|---|
| `Downloads/Personal_Cash_Flow_2026.xlsx` | Summary, Budget vs Actual, Monthly Cash Flow, Investments, **FIRE**, **Tax**, Assumptions, Transactions, Category Map | 07-07 | 07-07 (3 s after download; use count 2) | DEAD — most complete artifact, never adopted |
| `Downloads/personal_finance_v2.xlsx` | Dashboard, Budget, Budget vs Actual, Investments, Goals, **RBC Import, Scotia Import, Keyword Rules** | 03-16 | never reopened | DEAD — import pipeline designed, never fed |
| `Downloads/Vancouver_Housing_Sensitivity.xlsx` | Sensitivity (1 sheet, 12KB) | 05-11 | never reopened | DEAD — one-off scratch |
| `Downloads/cost_of_ownership.xlsx` | Model (1 sheet, 11KB) | 06-07 | never reopened | DEAD — one-off scratch; the only place rent-vs-own-ish analysis lives |
| `Documents/Personal Finance/personal_finance_template.numbers` | (Numbers) | 03-16, 2 min after v2 | — | DEAD — the "proper home" folder was created and abandoned the same day |

### 0.9 Corrections to the brief's premises (stated directly, per your §7)

1. **"A personal finance Excel model — this exists and works" — it does not.** What exists is four one-shot generated workbooks in Downloads, none ever edited, none reopened after creation day, none ever fed a transaction. `Personal_Cash_Flow_2026.xlsx` has the right *sheet inventory* (FIRE, BC Tax, Assumptions) to become the projection model the brief describes, but treating "Excel keeps forward projection" as *reusing a working system* would be designing around a ghost. Phase 1 must treat the projection model as something to be **stood up** (possibly seeded from that file), not preserved.
2. **The commitments ledger does not exist.** `vault/coach/commitments.md` was never created; the only `commitments.md` on the machine is a Lighthouse fixture containing canned sample data ("Renew passport", "Reply to Dana re: cabin weekend"). The Commitments database migrates **nothing** — it starts empty. That simplifies Phase 1.
3. **The journal does not exist.** Zero daily notes anywhere, daily-notes plugin on untouched defaults, no journal template, and `~/coding-journal` is an unrelated dev-tool project. The Obsidian side of your prose/records seam is currently **aspirational** — which doesn't invalidate the seam, but the spec should say honestly that on day one, Notion will be the only living half.
4. **Lighthouse was never deployed.** No Tailscale exposure, no iPad, no launchd beats, never pointed at the real vault, LLM provider never activated. Its value to this project is as a parts bin (CSV drop-folder ingestion, collector patterns), not as a running system to integrate with.
5. **Reassuring consistency:** the brief's BMO + RBC CSV assumption matches reality better than the old model did — `personal_finance_v2.xlsx` (March) had RBC + *Scotia* importers, and Downloads artifacts show a BMO job starting ~May 2026. Phase 1 will design for BMO + RBC as stated.

### 0.10 Anomalies & time-sensitive items

- **Zombie process:** the Lighthouse Fastify server (PID 86064) has been running since 07-07, serving frozen fixture data on 127.0.0.1:8080. Harmless (loopback only) but pointless. I have not killed it — say the word and I will.
- **`lighthouse/.env` was modified today at 15:52** (2026-08-19) — the only touch of that project in 37 days. Gmail credentials are set in it; no run followed. No git history exists to diff. If that was you, it doesn't change any verdict, but tell me if you're actively reviving Lighthouse — it changes Phase 2.
- **Garmin backfill window:** `sync.py --days` caps at 90 and the gap is 87 days, so the one-flag recovery path closes **~2026-08-22**. After that, `--since` still works (Garmin retains the data server-side), it's just a slightly different invocation, and cached tokens have expired either way so a fresh login is needed. Decision needed: do you want the May 24 → today vault gap backfilled at all, given Notion will receive weekly aggregates going forward?
- **Secrets hygiene:** live Google OAuth client credentials (`credentials.json`) and an expired token sit in `~/Downloads/mission-control/scripts/`; Garmin credentials in `Vault/Garmin/_sync/.env` (inside a vault with Obsidian Sync enabled). Worth relocating regardless of this project.
- The Google Cloud OAuth consent screen is in "Testing" mode → refresh tokens die after 7 days. Any revived Google integration must either publish the app or accept weekly re-auth — a Phase 2 design input.

### 0.11 Dataview query inventory (what the vault currently depends on)

Zero dataview usage exists outside Garmin/ and MissionControl/ (vault-wide grep). Full query list:

**Garmin — Dashboard.md (5 blocks):**
1. "This Morning" recovery snapshot — `date, readiness_score, readiness_level, hrv_last_night_avg, hrv_status, sleep_score, sleep_hours, sleep_hours_inferred, resting_hr`
2. Step rollup today/7d/30d — `date, steps`
3. Last-7-days recovery table — same fields as (1) minus readiness_level
4. Recent 10 activities — `date, type, name, distance_m, duration_s, avg_hr, training_load, aerobic_te`
5. Sleep-tracking gaps diagnostic — `date, wear_hours, resting_hr, min_hr, stress_qualifier, valid_sleep, sleep_hours`

**Garmin — Trends.md (4 blocks):** 30-day HRV w/ baselines (`hrv_last_night_avg, hrv_status, hrv_weekly_avg, hrv_baseline_balanced_low/high`); 30-day sleep by ISO week (`sleep_hours, sleep_score`); 90-day training load by type (`type, training_load, distance_m, duration_s`); 30-day RHR (`resting_hr, resting_hr_7day_avg`).

**Garmin — Weekly.md (2 blocks):** 12-week training volume (`distance_m, training_load, aerobic_te`); 12-week recovery averages (`hrv_last_night_avg, sleep_hours, sleep_score, resting_hr`).

**Garmin — Years.md (3 blocks):** all-time weekly recovery with inferred-sleep fallback (`sleep_inferred, sleep_hours_inferred, avg_sleep_hr, avg_sleep_hr_inferred` + recovery fields); all-time weekly training (`+ anaerobic_te`); all activities flat table.

**Garmin — Activities.md (1 block):** all-time activities table (same fields as Years' flat table + `training_effect`).

**MissionControl:** Mission Control.md — 1 dataviewjs (week grid + Sync GCal exec button) + 3 dataview + 6 Tasks blocks over `event_date, event_time, event_title, location, type, status, gcal_id`; daily-note-snippet.md and Weekly Review template — Tasks blocks + small event tables over `event_date`.

**Schema evolution warning for Phase 1:** frontmatter fields are not uniform across the 507 daily notes — `hrv_baseline_balanced_low/high` exist in 199/507, `avg_sleep_hr` in 176, `sleep_inferred` in 17. Queries tolerate nulls; any migration/aggregation script must too.

**Daily-note frontmatter schema (full):** `date, source, steps, step_goal, distance_m, calories_total, calories_active, resting_hr, min_hr, max_hr, resting_hr_7day_avg, avg_stress, max_stress, stress_qualifier, body_battery_high/low/charged/drained, moderate_minutes, vigorous_minutes, wear_hours, sleeping_hours, sleep_hours, sleep_deep_hours, sleep_light_hours, sleep_rem_hours, sleep_awake_hours, sleep_score, valid_sleep, hrv_last_night_avg, hrv_status, hrv_weekly_avg, hrv_baseline_*, readiness_score, readiness_level, training_status(+), [sleep_hours_inferred, avg_sleep_hr_inferred, sleep_inferred]`.

**Activity-note frontmatter schema:** `date, activity_id, type, name, start_time, distance_m, duration_s, moving_duration_s, calories, avg_hr, max_hr, avg_speed_mps, max_speed_mps, steps, aerobic_te, anaerobic_te, training_load, training_effect, vigorous_minutes, moderate_minutes`.

### 0.12 Salvage list (inputs to Phases 1–2, not designed yet)

- **Garmin `_sync`**: `extractors.py` (pure, tested against real payloads), `garmin_io.py` (429 backoff), the gap-fill/state pattern, and `discovery/` fixtures — directly reusable for a Garmin → weekly-aggregate feed. The data itself (507 daily + 61 activity notes) is the seed corpus for Weekly Log backfill *computed locally* — it never needs to hit the Notion API row-by-row.
- **mission-control**: `auth.js`/`setup-auth.js` OAuth scaffolding (needs re-auth + consent-screen decision); the inbox-scan scoring heuristic if email-derived suggestions ever return (v2 at best).
- **lighthouse**: the `drops/` CSV drop-folder pattern and `lib/csv.js` — the closest existing precedent to the money ingest design; `collectors/bank.js` as a starting point for BMO/RBC parsers.
- **Behavioral evidence as a design constraint** (your §5, now with data): three systems died specifically at the *manual recurring trigger* — the Garmin button (30 days), the calendar button (12 days), the Weekly Review that never happened even once. The only component that survived is the one that required zero clicks (a daemon nobody remembered). Phase 1–3 will treat "survives two weeks of total neglect" as a hard acceptance criterion and put every recurring manual step under a 10-second budget or on a monthly cadence.

### 0.13 Questions to confirm before Phase 1

1. **Confirm the all-DEAD baseline**: design proceeds as a cold restart — reuse code as libraries, treat no subsystem as live, nothing needs backward compatibility except the Garmin data corpus. (Recommended: yes.)
2. **Garmin gap backfill** (soft deadline ~08-22 for the easy path): backfill May 24 → today into the vault before we build anything, skip the gap entirely, or defer? My recommendation: run the backfill now — it's one command, it preserves continuity of the highest-value dataset you own, and Phase 2 will want the vault current as the local source of truth for weekly aggregates.
3. **Kill the zombie Fastify server** (PID 86064)? It serves fixture data on loopback; nothing depends on it. (Recommended: yes, and delete nothing.)
4. **Was the `lighthouse/.env` edit today (15:52) you?** If you're actively poking Lighthouse, Phase 2 should account for it; if not, it stays a parts bin.
5. **Spec repo location**: this file lives in a fresh repo at `~/notion-os/`. Fine, or name a different home?
6. **Finance reality check**: is `Personal_Cash_Flow_2026.xlsx` the "existing Excel model" the brief meant, or is there a living model somewhere I can't see (Google Sheets, work machine, iCloud)? Phase 1's Excel-boundary design changes materially depending on the answer.
7. **Journal**: given no prose currently exists in Obsidian, do you want the spec to keep the Obsidian half of the seam as-is (a home for future prose, no work invested), or should Phase 3 include a minimal journal bootstrap (daily-note template + one hotkey)? The latter is scope — I'd default to keeping it out of v1.

**Phase 0 checkpoint resolved 2026-08-19: confirmed with recommended defaults ("go").**

---

## Phase 1 — Schema design

Method: three independent designers (abandonment-resistant minimalist / data-modeling rigor / Notion-mechanics realist), two adversarial critics (abandonment red-team walking week-3 and month-2 neglect scenarios; Notion-mechanics verifier checking every rollup, formula, and API claim), one synthesis judge. 37 critique findings adjudicated; two critic-fatal findings shaped the final design (silent pipeline death; the Notion API's 25-relation-reference cap on rollup reads).

### 1.0 Shape of the design

**Five databases. One relation pair. One rollup. Ten formulas. Zero automations. Zero cross-database rollup chains.**

Design rules (carried into Phases 2–3):
- Relations exist only on low-volume, human-entered tables (People ↔ Interactions). High-volume or script-written tables are relation-free.
- Every uniqueness/cardinality invariant is owned by the writing script's query-then-upsert — Notion cannot enforce any of them. Keys: `Weekly Log.Week` (title), `Monthly Money.Month` (title), `Transactions.Hash` (rich_text).
- Aggregates are recomputed from a Notion query, never from the CSV parse — so manual category fixes always flow through.
- The system's single rollup (People.Last Contact) is UI-render-only, never read via API — the API computes rollups from at most 25 relation references, which makes API rollup reads silently wrong at volume. Banned as a non-goal.
- Every pipeline fails loudly (macOS notification) or not at all. Phase 0's central lesson is baked in: the Garmin sync died silently for 87 days and nobody noticed — so "the daemon is reliable" is never assumed, it is monitored.

The recurring human obligations in the entire system, exhaustively: (1) <10-second social capture, event-driven; (2) one ~15-minute money sitting per month (export 3 CSVs, run one command, type 6 balance numbers). Nothing else recurs. Nothing is weekly.

### 1.1 Databases

#### 1.1.1 Weekly Log — health + social, one row per ISO week

No human ever writes this table. A launchd job (Mondays ~07:00) aggregates the local Garmin vault corpus and upserts by Week title. A row is created even for a zero-data week, so a **missing row always means script failure**. ~52 rows/year forward; one-time backfill of ~85 rows (2025-W01 → current) computed locally from the 593-note corpus. Weekly API cost ≈ 9–17 calls (amended by §2: the full trailing-4-week rewrite buys universal convergence). Zero relations, zero rollups.

| Property | Type | Definition |
|---|---|---|
| Week | title | ISO week key, e.g. `2026-W34`. Unique; **the idempotent upsert key** (API title-equals filter). Matches Python `isocalendar()`. |
| Week Start | date | Monday of the ISO week. Sort key / chart axis. |
| Month Key | formula | `formatDate(prop("Week Start"), "YYYY-MM")` — exists solely so the By Month view can group with free per-group averages. |
| Weight Avg | number | kg, 1 decimal. Weekly mean of smart-scale weigh-ins flowing through Garmin Connect body-composition (§1.12.1: scale purchase confirmed; columns stay in v1). Never a manual cell. Blank = no weigh-ins yet — blank, not 0, until the scale arrives. |
| Weight Delta | number | Signed, 1 decimal. This week minus previous non-blank week, **script-computed at write time** (Notion formulas cannot reference the previous row). Blank — never 0 — when either side lacks data. |
| Training Sessions | number | Count of Garmin activities that week. |
| Training Load | number | Sum of activity `training_load` that week. |
| PT Sessions | number | Count of activities whose Garmin type is in a config allowlist (confirmed §1.12.2: PT will be logged as a distinct activity type; allowlist seeded with `strength_training` and adjusted to whatever type his device actually records — corpus currently has none, so backfilled weeks honestly read 0). |
| Sleep Avg | number | Hours, 1 decimal. Mean of `sleep_hours` over `valid_sleep` nights, falling back to `sleep_hours_inferred` (mirrors Years.md logic; nulls tolerated per §0.11). |
| Sleep Score | number | Mean of `sleep_score` over nights with a value. |
| RHR | number | Mean `resting_hr`, bpm. |
| HRV | number | Mean `hrv_last_night_avg`, ms (partial historical coverage; nulls tolerated). |
| Social Touches | number | Count of Interactions with Date in [Week Start, Week Start+6], **script-computed via one date-range query** — deliberately not a rollup (a rollup would force a week-relation onto every capture). Recomputed over the trailing 4 weeks each run so late-logged touches converge. |
| Days With Data | number | 0–7 daily notes carrying Garmin data that week. Explicit zero-data marker **and the watchdog sensor**: 0 fires a macOS notification (upstream sync presumed dead). |

#### 1.1.2 Interactions — append-only social event log

The one table where capture speed is existential: exactly four properties, only People requiring input. Group event = one row, N people. ~200–400 rows/year + ~30 backdated seed rows at setup. The weekly script self-heals the two rot vectors: empty Date := `created_time`; blank titles := `MMM D · Type`.

| Property | Type | Definition |
|---|---|---|
| Name | title | Optional, blank at capture. Weekly script backfills blanks so views never fill with "Untitled". |
| Date | date | Template "Touch" pre-fills dynamic @Today; the iOS Shortcut sets now explicitly; script patches empties to created_time. |
| People | relation | → People, multi-page, dual property `Interactions`. **The only required input at capture.** Typeahead-created stubs are caught by People's Needs Tier view. |
| Type | select | `1:1` (default — the modal case costs zero taps), `Group`, `Call`, `Async`. |

Notes go in the free page body, never a property. No week relation, no initiated-by checkbox, no required title — each removed specifically to protect the <10s budget.

#### 1.1.3 People — the CRM, and the system's only rollup / now()-formulas

~30–40 rows entered once at setup. Staleness math recomputes at view render with zero writes, so it stays correct under total neglect. Primary Obsidian→Notion link target (pure-ID URLs). An iOS home-screen widget stays pinned to the Due view.

| Property | Type | Definition |
|---|---|---|
| Name | title | Entered once. |
| Tier | select | Options are exactly `A`, `B`, `C` (cadence legend lives in the property description — parentheticals in option names would break the formula match). A = inner (14d), B = close (30d), C = keep-warm (90d). |
| Cadence Override | number | Optional per-person override in days; usually empty. |
| Effective Cadence | formula | `ifs(!empty(prop("Cadence Override")), prop("Cadence Override"), prop("Tier") == "A", 14, prop("Tier") == "B", 30, prop("Tier") == "C", 90, 60)` — the trailing 60 is a fallback so **no state can silently never-nag**. |
| Interactions | relation | Dual side of Interactions.People; auto-populates on capture. |
| Last Contact | rollup | Relation: Interactions · Target: Date · Aggregation: **Latest date**. The system's only rollup; UI-render-only, never read via API. |
| Days Since | formula | `if(empty(prop("Last Contact")), 9999, dateBetween(now(), prop("Last Contact"), "days"))` — 9999 floats never-contacted people to the top; recomputes free at view load. |
| Due | formula | `prop("Days Since") >= prop("Effective Cadence")` (boolean). Powers the default Due view. |

#### 1.1.4 Transactions — system of record for money actuals

Every BMO/RBC CSV line lands here exactly once via the monthly import. `categories.yml` (the config file, not Notion) owns the taxonomy. **Kind is a formula derived from Category**, so the one manual edit humans make here (fixing a category) can never desync flow classification. Spend-by-category is native grouped views, not a derived table. No relations. ~200–400 rows/month.

| Property | Type | Definition |
|---|---|---|
| Description | title | Normalized merchant string; lossy normalization preserves the raw line in the page body. |
| Date | date | Transaction date where the bank provides it, else posted date — fixed per account in parser config; the **same raw field always feeds the Hash** so keys are stable across re-exports. |
| Amount | number | CAD, signed: inflow +, outflow −, from the account's own perspective; importer normalizes each bank's sign quirks. Refunds keep the original spend category → category sums are net-of-refunds automatically. |
| Account | select | `RBC Chequing`, `RBC CC`, `Scotia Visa` (corrected per §1.12.4 — the brief's "BMO" was the employer, not the bank; any further RBC accounts, e.g. Savings, become auto-created options). Set from which CSV the row came. Select, not relation (nothing needs the lookup). |
| Category | select | Flat select seeded from `categories.yml` (seeded in turn from personal_finance_v2.xlsx's Keyword Rules sheet). **Naming convention is load-bearing for Kind**: plain names for spend (Groceries, Dining, Transport, Housing, Subscriptions, Health, Golf, Gifts, Travel, Shopping, Fees, Cash, Misc, Uncategorized); `Income — Salary`, `Income — Other`; `Contribution — TFSA/RRSP/FHSA/Taxable`; `Transfer — CC Payment`, `Transfer — Internal`. The one property humans edit. |
| Kind | formula | `ifs(contains(prop("Category"), "Contribution — "), "Contribution", contains(prop("Category"), "Income — "), "Income", contains(prop("Category"), "Transfer — "), "Transfer", "Expense")`. Transfer rows contribute 0 to every aggregate — the double-counting firewall (CC payments appear in both card and chequing CSVs). |
| Month | formula | `formatDate(prop("Date"), "YYYY-MM")` — groupable in views, API-filterable (formula string equals) for the importer's window queries. |
| Hash | rich_text | First 16 hex of `sha256(account_key\|raw_date\|raw_amount\|raw_description\|dup_index)` where dup_index is the ordinal among byte-identical lines in the same CSV — **two identical coffees on one day survive dedupe**. The idempotency key; importer pre-fetches existing hashes in 2–4 paginated window queries and diffs locally (never one query per row). Manual rows: `manual-<uuid>`. |
| Import Batch | rich_text | Run id, e.g. `2026-09-01·rbc-cc` — lets a bad import be bulk-identified and repaired. (rich_text, not select — the option list would grow unbounded.) |

#### 1.1.5 Monthly Money — the roll-up and home of THE net-worth number

One wide row per month, always created by the import script. Aggregate columns are recomputed from a post-import Notion query (never frozen CSV-parse sums); a `re-aggregate YYYY-MM` subcommand reruns just that after fix-up sessions. Balance columns replace both a Balances DB and an Accounts DB (see decision T6b). This row is the system's entire recurring ritual: ~15 min/month.

| Property | Type | Definition |
|---|---|---|
| Month | title | `YYYY-MM`. Unique; idempotent upsert key; matches Transactions.Month by construction. |
| Month Start | date | First of month. Sort/chart key. |
| Income | number | Script: sum(Amount) where Kind = Income. |
| Spend | number | Script: −sum(Amount) where Kind = Expense, stored positive (net of refunds; Transfers/Contributions excluded by Kind). |
| Surplus | formula | `prop("Income") - prop("Spend")`. Contributions are *deployment* of surplus, not a reduction of it. |
| Savings Rate | formula | `if(prop("Income") > 0, (prop("Income") - prop("Spend")) / prop("Income"), 0)` (percent format; 0 on a zero-income month = "undefined", noted in the description). |
| Contrib TFSA / RRSP / FHSA / Taxable | number ×4 | Script: sum per `Contribution — *` category, sign-normalized positive. Explain the month-over-month net-worth delta; **never feed the Net Worth formula**. |
| Bal Chequing / TFSA / RRSP / FHSA / Taxable | number ×5 | **Hand-entered monthly from statements — ground truth, never derived** (summing flows drifts with every market move). BMO/RBC transaction CSVs don't reliably carry balances; CSV prefill is an opportunistic Phase 2 idea, not assumed. |
| Liabilities | number | Hand-entered: CC balances carried past statement date + other debt. **Enter 0 explicitly** — empty blocks Net Worth by design. |
| Net Worth | formula | `if(empty(prop("Bal Chequing")) or empty(prop("Bal TFSA")) or empty(prop("Bal RRSP")) or empty(prop("Bal FHSA")) or empty(prop("Bal Taxable")) or empty(prop("Liabilities")), toNumber(""), prop("Bal Chequing") + prop("Bal TFSA") + prop("Bal RRSP") + prop("Bal FHSA") + prop("Bal Taxable") - prop("Liabilities"))`. **THE one authoritative net-worth number.** The completeness guard makes a partial month *visibly blank* instead of plausibly wrong; the blank doubles as the dead-man switch trigger and the export gate. |

### 1.2 ER diagram

```
┌───────────────────────────┐ 1        * ┌────────────────────────────┐
│          People           │◄───────────│        Interactions        │
│───────────────────────────│  dual rel  │────────────────────────────│
│ Name             title    │            │ Name  title (blank; script │
│ Tier             select   │            │        backfills)          │
│ Cadence Override number   │            │ Date  date (@Today default;│
│ Effective Cadence formula │            │        script patches      │
│ Interactions     relation │            │        empty→created_time) │
│ Last Contact     rollup ──┼─ latest(Interactions.Date)              │
│ Days Since       formula  │            │ People relation ───────────┼─► People
│ Due              formula  │            │ Type  select (default 1:1) │
└───────────────────────────┘            └─────────────┬──────────────┘
   ▲ human: ~35 rows once                 human: <10s capture (iOS
   │ + widget pinned to Due view          Shortcut → API, or template)
   │                                                   │ weekly script COUNTS by
   │                                                   │ date range (trailing 4 wks)
   │                                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│ Weekly Log          NO relations · NO rollups · 1 formula          │
│ Week(title,KEY) WeekStart MonthKey WeightAvg WeightΔ TrainSessions │
│ TrainLoad PTSessions SleepAvg SleepScore RHR HRV SocialTouches     │
│ DaysWithData(watchdog sensor)                                      │
└────────────────────────────────────────────────────────────────────┘
   ▲ written ONLY by weekly launchd job (vault Garmin corpus → local
     compute → upsert; osascript notification on error/0-data/stale vault)

Obsidian vault (593 daily + 72 activity notes — raw stays local forever)
   └─ local aggregation ──► Weekly Log (backfill ~85 rows + weekly upsert)

Bank CSVs (BMO CC, RBC CC, RBC Chequing — manual monthly export → drops/)
   └─ parse + categories.yml rules ──► ┌───────────────────────────────┐
                                       │ Transactions   NO relations   │
                                       │ Description(title) Date       │
                                       │ Amount(signed CAD)            │
                                       │ Account(select) Category(sel) │
                                       │ Kind(FORMULA from Category)   │
                                       │ Month(formula 'YYYY-MM')      │
                                       │ Hash(rich_text+dup_index,KEY) │
                                       │ Import Batch(rich_text)       │
                                       └──────────────┬────────────────┘
              importer RE-QUERIES Notion post-import  │  (no rollup crosses
              and sums by Kind/Category locally       ▼   this line)
   ┌──────────────────────────────────────────────────────────────────┐
   │ Monthly Money      NO relations                                  │
   │ Month(title,KEY) MonthStart │ script: Income Spend Contrib ×4    │
   │ human: Bal ×5 + Liabilities                                      │
   │ formulas: Surplus SavingsRate NET WORTH (guarded) ◄── THE number │
   └──────────────────────────────┬───────────────────────────────────┘
        monthly launchd dead-man  │  export CSV once Net Worth non-blank
        switch watches this row   ▼  (one-way, never back)
                    Excel projection workbook (NEW BUILD; FIRE / BC Tax /
                    Assumptions seeded from Personal_Cash_Flow_2026.xlsx)
```

### 1.3 Day-one views (part of the design, zero writes)

| Database | View | Config |
|---|---|---|
| People | **Due** (default) | Filter: Due checked. Sort: Days Since desc. **Page-load limit 10** — caps the post-lapse guilt wall to an actionable list. Pinned as an iOS home-screen widget; this view *is* the social ritual. |
| People | Directory | All rows, alphabetical: Name, Tier, Cadence Override, Last Contact. |
| People | Needs Tier | Filter: Tier empty — catches capture-typeahead stubs so the 60-day fallback stays temporary. |
| Interactions | Recent (default) | Sort: Date desc. Default template "Touch" (@Today, Type 1:1) set for all views; capture sheet shows exactly Date / People / Type. |
| Weekly Log | Timeline (default) | Sort: Week Start desc. Column calcs: averages on Weight/Sleep/Score/RHR/HRV; sums on Load/Sessions/Touches. |
| Weekly Log | By Month | Group by Month Key desc, same per-group calcs — the monthly health trend readout. |
| Transactions | By Month (default) | Group by Month desc, filter Kind ≠ Transfer, per-group Sum(Amount). (Honest month-scoping: Notion has no calendar-"this month" filter; a rolling filter would silently desync from Monthly Money.) |
| Transactions | Last 30 Days by Category | Filter: Kind = Expense AND Date within past 30 days (named honestly as rolling). Group by Category, per-group Sum. |
| Transactions | Uncategorized | Filter: Category = Uncategorized, Date desc. **The maintenance queue** — its row count is the "surfaced when it grows" signal; fixes propagate via Kind (instant) and the next re-aggregate run. |
| Transactions | Contributions | Filter: Kind = Contribution, group by Category — per-shelter totals for free. |
| Monthly Money | Ledger (default) | Sort: Month desc, all columns. A **blank Net Worth cell is the built-in "month incomplete" nag**. |
| Monthly Money | Export | Month asc, exactly the 16 export columns in CSV order — doubles as manual export fallback (Notion's "Export view as CSV"). |

### 1.4 Social capture: the <10-second path, honestly counted

The budget is counted **from lock screen, including app launch** — the Notion app path is 10–15s on a cold start, which is over budget on the one flow named existential (all three designers initially made the warm-path accounting error; the critics caught it).

- **Primary (v1, ~3–5s): an iOS Shortcut** (Action Button / lock screen / home screen) that POSTs the Interaction directly to the Notion API — Date = now, Type = 1:1, person picked from a Shortcut menu built from a local name→page-id cache the weekly script refreshes. No app launch, ~1 hour to build, no server.
- **Fallback (~8–10s warm): Notion widget** → Interactions "+ New" → template "Touch" applies @Today + 1:1 → tap People, type 2–3 letters, pick, swipe away. Used for group events and anything needing nuance.
- **Self-healing:** the weekly script patches empty Dates to created_time and blank titles to `MMM D · Type`; the Weekly Log count re-queries a trailing 4-week window, so a rushed or late entry can never corrupt anything downstream.
- Both paths get **measured on the actual phone during the build weekend**; the template-@Today behavior gets verified on-device.

### 1.5 Excel boundary

**The one authoritative net-worth number is `Monthly Money.Net Worth`** (guarded formula over six hand-entered statement balances, §1.1.5). Nothing else — Notion view, script, or Excel — computes a competing actual; everything derives.

**Transport:** one file, `exports/monthly_money.csv` — a full dump of Monthly Money with columns: Month, Income, Spend, Surplus, Savings Rate, Contrib TFSA, Contrib RRSP, Contrib FHSA, Contrib Taxable, Bal Chequing, Bal TFSA, Bal RRSP, Bal FHSA, Bal Taxable, Liabilities, Net Worth. Written by the import script's final step **and regenerated by the monthly watchdog once the month's Net Worth becomes non-blank** (fixing the sequencing trap where a same-run export always predates balance entry); blank-Net-Worth months are skipped; a manual `export` subcommand exists. Category-level detail is *not* part of the standing interface — if the projection model ever wants it, the export script pivots it locally from a paginated Transactions query, never from an API rollup read.

**The Excel side is a new build** (per §0.9.1 there is no working model to keep): a projection workbook seeded structurally from Personal_Cash_Flow_2026.xlsx's FIRE / BC Tax / Assumptions sheets, with its Transactions and Budget-vs-Actual sheets deleted. Its t=0 is the latest complete row's Net Worth plus per-account balances (needed for TFSA/RRSP/FHSA room and tax scenarios); run-rate inputs are trailing-12-month means referencing the imported CSV, never hand-typed. Strictly one-way Notion → Excel; transaction-level detail never crosses the boundary.

### 1.6 Migration map

**Migrates (transformed, one-time, computed locally — raw rows never hit the API):**
- The Garmin corpus (now 593 daily + 72 activity notes, continuous 2025-01-03 → 2026-08-18 after today's backfill) → aggregated locally into ~85 Weekly Log rows, written once through the throttled queue. Aggregation tolerates the non-uniform frontmatter (§0.11) and applies Years.md's inferred-sleep fallback.
- `personal_finance_v2.xlsx` "Keyword Rules" sheet → seeds `categories.yml`.
- `Personal_Cash_Flow_2026.xlsx` → seeds the *sheet structure* of the new Excel projection workbook. No data migrates because none is real.
- ~30 backdated seed Interactions (one per person, rough real last-contact dates) entered at setup so the Due view works from hour one.

**Stays put:** the raw Garmin daily/activity notes remain in the vault permanently as the local source of truth — Notion receives aggregates only, forever. Obsidian remains the designated home for future prose (currently empty — on day one Notion is honestly the only living half of the seam). Linking one-way Obsidian → Notion using **pure-ID URLs** (`https://www.notion.so/<32-hex-id>` — survive renames/moves; never slugged or `?v=` URLs); primary targets are People pages and Monthly Money rows.

**Salvaged as code, not data (Phase 2 inputs):** `extractors.py` + `garmin_io.py` + the last_sync gap-fill pattern → weekly aggregator; Lighthouse's `drops/` CSV-folder pattern + `lib/csv.js` + `collectors/bank.js` → money-ingest skeleton; mission-control OAuth scaffolding only if a Google integration ever returns (blocked anyway on the 7-day "Testing"-consent token problem).

**Abandoned outright:** Mission Control as a system (events, templates, dashboard, scripts, expired OAuth); all five Dataview dashboards (their field lists informed Weekly Log and are superseded); the Lighthouse runtime (zombie process killed 2026-08-19); the fixture commitments.md; Welcome.md, the PARA skeleton, the 0-byte Documents.md; personal_finance_v2.xlsx beyond the Keyword Rules seed; personal_finance_template.numbers; Vancouver_Housing_Sensitivity.xlsx; cost_of_ownership.xlsx (content may inform a v2 rent-vs-own tab). Also: relocate the exposed secrets flagged in §0.10 during the build weekend.

### 1.7 Where this design overrules your proposal (per your §7: direct, unsoftened)

1. **Social touch count as a rollup — modified.** A true rollup requires a week-relation set on every capture (rollups can't date-filter, so the relation *is* the filter). That picker costs 5–10 seconds on a phone: your entire budget spent on plumbing, on the flow you named the failure point. It's a script-written number from one date-range query instead — same number, zero capture cost.
2. **Spend total / savings rate on Weekly Log — rejected.** You decided money arrives monthly. A weekly spend figure is either stale fiction three weeks out of four or it forces weekly CSV exports — reinstating the exact manual trigger that killed three systems. Money lives at exactly one grain per fact: per-event in Transactions, per-month in Monthly Money.
3. **"One write per week" as a manual act — modified.** Your own Phase 0 history: every manual trigger died within 30 days; the only survivor required zero clicks. The weekly row is written by a launchd job — and because the "reliable daemon" premise is *also* falsified (§0.10: 87 silent days), the job fails loudly: macOS notification on error, zero-data week, or stale vault.
4. **Weight avg + delta — modified.** No weight field exists anywhere in your Garmin frontmatter. If Garmin body-composition data exists for your account (10-minute pre-build API test), the script fills both columns; if not, both are cut from v1. A manual weekly cell is banned — the "empty cell as reminder" variant is guilt-debt engineered in.
5. **Commitments DB in v1 — rejected.** The source file never existed and no agent exists as the write path. An empty database whose only writer is you, manually, recurringly, is a precise rebuild of the artifact that died three times. Deferred to v2, shipped in the same change as the first agent that writes to it.
6. **Goals & KRs — modified.** A goals database only pays off through a review cadence, and your review cadence has a 0% historical survival rate (it never ran once). v1 is one static "2026 Goals" page pinned at the top; a Goals DB is v2, gated on any review cadence surviving 8+ weeks.
7. **Contributions "logged as rows" + "balances + contributions → net worth" — modified, twice.** (a) A contribution *is* a transaction — it arrives in the chequing CSV; a separate DB double-records the same money movement. Contributions are Transactions rows (`Kind = Contribution`, destination in the category). (b) Contributions must **not** feed net worth: summing flows drifts from reality with every market move, and two derivation paths mean two disagreeing numbers — exactly what you forbade. Net worth = statement balances only; contribution totals sit alongside to explain the delta.
8. **Initiated-by-me checkbox — rejected.** It drives no v1 view; its payoff is reciprocity analysis after months of data (your own rule sends that to v2), an optional checkbox produces unusable data (unchecked = "they initiated" or "didn't bother"?), and every optional field on the capture sheet taxes the 10-second budget. v2 as a Me/Them/Mutual select if ever wanted.
9. **Per-person cadence target — modified.** Hand-typing ~30 cadence numbers is setup friction that drifts, and a person with no cadence must not silently vanish from the Due view. Tier drives 14/30/90 via formula, optional per-person override, 60-day fallback so no state can never-nag.
10. **"<10s via the Notion app" — modified.** Honest timing includes the 3–6s iOS cold start: 10–15s cold, over budget. v1 primary is a direct-API iOS Shortcut (~3–5s from lock screen); the app path is the fallback. Both measured on your phone during the build.
11. **"Excel keeps only forward projection" framed as keeping the existing model — modified.** The boundary is right; the premise is a ghost (§0.9.1). The projection workbook is named as a **new build**, seeded from Personal_Cash_Flow_2026.xlsx's structure, consuming exactly one export CSV.

### 1.8 Decision log (contested points, adjudicated)

| # | Tension | Decision |
|---|---|---|
| T1 | Social count: rollup / script / drop | Script-written, trailing-4-week recompute (unanimous + critic fix). |
| T2 | Weekly money fields | Rejected — one grain per fact. |
| T3 | Weight delta | Script-computed at write time; blank, never 0-filled. |
| T4 | Commitments in v1 | Rejected; v2 with its first agent writer. |
| T5 | Goals/KRs | Static page in v1; DB gated on a review cadence surviving 8+ weeks. |
| T6a | Contributions DB | Folded into Transactions (typed rows) — a second DB is a double-count by construction. |
| T6b | Balances: snapshot rows vs columns | Columns on Monthly Money. Both verified sound; columns win on abandonment (6 typed numbers vs 12–24 relation-picker interactions/month) and delete 2 DBs + 2 relation pairs + a rollup. Revisit only if per-account attribution analysis is ever wanted (v2). |
| T6c | Spend-by-category | Native grouped views; a materialized Category×Month table silently drifts on every recategorization. |
| T7 | Authoritative net worth | `Monthly Money.Net Worth`, guarded formula over statement balances only. |
| T8 | Month keys / upserts / staleness | formatDate month keys (groupable + API-filterable); queryable idempotency keys with pre-fetched diff; now()-formulas only on People, never API-read; zero load-bearing automations. |
| — | Kind: parser-set select vs formula | **Formula derived from Category prefixes** — a manual category fix crossing flow classes can never strand a stale flow label (critic-major, generalized to all three designs). |
| — | Month aggregates: CSV-parse sums vs live rollups | **Neither** — recomputed from a post-import Notion query + `re-aggregate` subcommand. CSV sums desync from manual fixes; API rollup reads hit the 25-ref cap (critic-fatal). |
| — | Silent pipeline death (critic-fatal, all designs) | Push-style surfacing with zero new infra: weekly osascript notifications (error / 0-data / stale vault) + monthly launchd dead-man switch that nags weekly while last month's row is missing or Net Worth blank, self-clearing. Token-refresh runbook in the repo. |
| — | Capture path | iOS Shortcut promoted to v1 primary; app widget fallback; measure both on-device. |
| — | Day-one guilt wall | Seed ~30 backdated Interactions + cap Due view at 10 rows — a ranked list is actionable, a 30-person 9999-wall is a reproach (this user's documented abandonment trigger). |
| — | Export timing | Gated on completeness, not sequencing: skip blank-Net-Worth months; watchdog regenerates once balances land. |

### 1.9 v2 — deferred (clearly labelled, per your §5)

Commitments DB (ships with its first agent writer; sketch reserved) · Goals/KR database with check-ins (gated on 8+ weeks of surviving review cadence) · initiated-by as Me/Them/Mutual select + reciprocity analytics · Balances/Accounts snapshot-row architecture (mechanics verified; ergonomics lost) · CSV-derived balance prefill (gated on whether BMO/RBC exports carry balances) · LLM-assisted categorization of the Uncategorized queue · split transactions & cash itemization (v1: one row, dominant category; ATM = "Cash" at withdrawal) · materialized Category×Month table (only if the export pivot demonstrably can't serve) · TFSA/RRSP/FHSA contribution-room tracking (Excel Assumptions first) · weekly money pulse column (only if genuinely missed) · live bank sync (only if the monthly ritual fails twice despite the dead-man switch) · email/calendar integration (blocked on the OAuth Testing-mode token problem anyway) · Obsidian journal bootstrap (§0.13.7 default) · daily-granularity health data / steps/body-battery/stress aggregates / any Dataview dashboard rebuild · notifications beyond the two watchdogs · rent-vs-own tab seeded from cost_of_ownership.xlsx · net-worth trend columns (script-written; Excel derives free meanwhile) · Interactions By-Week grouped view.

### 1.10 Non-goals

- No Plaid or live bank connections — manual monthly CSV export into `drops/` is the permanent v1 ingest.
- No hosted services, webhooks, or servers — local scripts via launchd or by hand.
- No daily health rows in Notion — Garmin raw stays in the vault forever; aggregates only.
- No hand entry of anything a device or CSV already knows. The only recurring manual entries in the system: <10s capture (event-driven) and the ~15-minute monthly money sitting.
- No weekly review ritual and no ritual dependency — every view must be correct under total neglect; nothing requires human action more often than monthly.
- No manual weight (or any health) entry cell — automated source or the column is cut.
- No silent failure modes — every pipeline fails loudly (macOS notification) or not at all; a missing row always means something detectable.
- No LLM or agent writes anywhere in v1 — every automated write is a deterministic script.
- No budgeting/envelope system or category targets — v1 observes spend, it does not police it.
- No double-entry bookkeeping — single-entry with `Kind = Transfer` as the netting mechanism.
- No derived/summary databases where a native view answers the question.
- No net-worth computation anywhere except the guarded formula; no Excel write-back, ever.
- No load-bearing Notion automations or status-property workflows.
- No Notion → Obsidian links (no `obsidian://` URIs in Notion), ever.
- No API reads of any Notion rollup (25-relation-reference cap makes them silently wrong); the single rollup is UI-only.
- No multi-currency (CAD only), no split transactions, no dashboards beyond native views.

### 1.11 Build-weekend sizing & open questions

**Sizing:** 5 databases / 54 properties / 1 relation pair / 1 rollup / 10 formulas / 12 views / 1 template / 0 automations. Hand setup ≈ 1 hour (~30 People + ~30 seed Interactions + one Goals page). Two scripts (`weekly_rollup.py`, `import_transactions.py` — both salvage-assembled), two launchd plists (weekly rollup; monthly dead-man switch) *(superseded by §2: four entrypoint scripts, three plists — the daily Garmin wrapper was implicit here)*, one iOS Shortcut (~1h). API budget: weekly ~5–8 calls; monthly import ~220–420 calls ≈ 2–4 min at 3 req/s; backfill ~85 creates once. Day-one utility: ~85 weeks of backfilled health history, a seeded capped Due view, sub-5-second capture, first money import the same weekend.

### 1.12 Phase 1 checkpoint — resolved 2026-08-19

1. **Weight**: a smart scale will be connected. Design consequence: the scale must land its weigh-ins in **Garmin Connect** so the existing pipeline stays single-source (vault-first, aggregates to Notion) — in practice that means a Garmin Index-family scale (native sync) or any scale with a maintained Garmin Connect bridge. Both weight columns stay in v1 and read blank until the scale arrives; the weekly aggregator consumes `weight_kg` from daily-note frontmatter (Phase 2 extends the extractors with Garmin's body-composition endpoint). Buying the scale is a plan.md line item, not a blocker.
2. **PT sessions**: confirmed — PT will be logged as a distinct Garmin activity type. Column stays; config allowlist, seeded `strength_training`. Corpus currently contains golf ×49, running ×16, treadmill_running ×3, lap_swimming ×3, indoor_cycling ×1 — zero PT yet, so backfilled weeks read 0 honestly.
3. **Categories**: seed list accepted verbatim; hardens into `categories.yml`.
4. **Accounts**: corrected to **RBC everything + Scotia Visa** — the brief's "BMO" was the employer (Phase 0's job-change evidence), not the bank, and personal_finance_v2.xlsx's RBC + Scotia importers were right all along. Account select: `RBC Chequing`, `RBC CC`, `Scotia Visa`; parsers needed for the RBC CSV format (shared across RBC account types) and the Scotia Visa CSV format. Five balance columns stand.
5. **Notion plan tier**: answer was ambiguous; immaterial to the design (charts are cosmetic). Assumed free tier until said otherwise.
6. **The 11 overrules in §1.7: accepted.**

**Phase 1 checkpoint resolved — schema confirmed. Phase 2 follows.**

---

## Phase 2 — Sync architecture

Method: two pipeline architects (health spine / money pipeline), each grounding every reuse claim by reading the actual salvage code line-by-line; one failure-mode red team that walked neglect scenarios end-to-end and verified platform claims (17 findings: 2 fatal, 6 major, 9 minor); one synthesis. **Every red-team finding was adopted** — each fix was cheaper than the failure it prevents. The two fatals: (1) a dead-man switch targeting only "the previous month" permanently orphans a month after two skipped sittings — fixed with a trailing-6-month window; (2) journaling import creates in batches of 25 reopens the exact duplicate window the journal exists to close — fixed with per-create journal flushes plus a batch-id resume query.

### 2.0 Shape

**Three launchd jobs. Two manual recurrences. Two repos. Zero servers.**

| Cadence | launchd job | What it does |
|---|---|---|
| Daily 07:15 | `com.notion-os.garmin-daily` | `garmin_daily.py` → vault Garmin sync (wrapped, locked, loud-on-death) + meta-watchdog over the two weekly jobs |
| Monday 07:40 | `com.notion-os.weekly-rollup` | `weekly_rollup.py` → vault → Weekly Log upsert, Interactions self-heal, offline-capture replay, people-cache export, watchdog |
| Friday 09:00 | `com.notion-os.deadman` | `deadman_check.py` → nag while any month in a trailing 6-month window lacks a complete Monthly Money row; regenerate the Excel export on change |

All three: `RunAtLoad=true` with per-script same-day/same-week debounce (a job whose time passes during sleep runs on wake; a powered-off machine catches up at next login — no starvation corner). Manual recurrences, exhaustively: the <10s capture (event-driven) and the ~15-minute monthly money sitting (deliberately unscheduled — it needs fresh bank exports only a human can fetch; **the automation is the nag, not the run**).

The watchdog topology is symmetric — no silent-death corner survives: the daily job watches both weekly jobs (state stale >9 days → notify, once per staleness episode, suppressed when the machine itself was off); the weekly job watches the daily (last attempt >3 days → notify); a missing Weekly Log row is the human-visible backstop; and `install.sh` refuses to install until a **test notification is human-confirmed** (a silently-denied osascript channel would recreate the 87-day failure one layer up — every notify is also mirrored to the log).

### 2.1 Scripts

#### 2.1.1 Vault Garmin sync — revival + weight extension (`Vault/Garmin/_sync/`, existing repo)

Runs untouched except **three files, three commits** (pushed to its GitHub remote): `extractors.py` gains `body_comp_fields` (~25 lines in the existing `_num/_round/_in_range` idioms, `WEIGHT_KG_RANGE = (30.0, 250.0)`); `sync.py` gains one fetch entry (body composition on date D — a calendar-day metric like steps, no D+1 shift) and one `fm.update` line; `auth_test.py` line 47 repoints dotenv at `~/.config/notion-os/garmin.env` (the §0.10 secret relocation; the vault `.env` is deleted). `discovery.py` gains a body-comp probe — **the gate before trusting field names on scale-arrival day**. Untouched and load-bearing: `garmin_io.fetch()` (the new endpoint inherits the whole 429-backoff/retry/404 policy by being wrapped in it), `notes.py` body-preservation, `state.py`, the `GAP_FILL_LOOKBACK=2` (load-bearing for D+1 sleep attribution — must survive). Zero-weigh-in behavior is spec-sane by construction: empty payload → `{}` → weight columns stay blank; a wrong payload assumption can never write garbage.

Never invoked by launchd directly — only through `garmin_daily.run_vault_sync()`.

#### 2.1.2 `scripts/garmin_daily.py` (new, ~150 lines)

The scheduled wrapper that makes the vault sync unkillable-by-gap and loud-on-death. Owns the **one shared blocking `fcntl` lock** around every `sync.py` invocation (`state/garmin-sync.lock`) — fixing the coalesced-wake race where a Monday wake fires 07:15 and 07:40 together against `notes.write_daily`'s lock-free read-truncate-rewrite (verified body-loss vector). Freshness skip: `last_sync` today + success <6h → no subprocess. Gap chooser (simplified per red-team: `--days` excludes today): gap ≤14 → default gap-fill; gap >14 → `--since <last_sync − 2d>`. **Auth classification** (the 87-day lesson, done right): only `GarminConnectAuthenticationError` produces the friendly "Authentication failed" string — lockout/MFA/SSO deaths arrive as raw tracebacks, so the wrapper classifies auth-suspect on a substring set ({Authentication failed, GarminConnectAuthenticationError, TooManyRequests, Too many login attempts, MFA, Login failed}) → **immediate** notification with the runbook, sets an `auth_dead` flag that **stops the daily credential retry** (never drive a locked-out account deeper at 3 logins/day; re-notify every 3rd day; flag self-clears when `last_sync.json` advances). Other failures: quiet for 2 consecutive, notify on the 3rd and after. Plus the meta-watchdog over rollup and deadman state described in §2.0.

#### 2.1.3 `scripts/weekly_rollup.py` (new, ~470 lines)

The health spine, in order: **(0)** lock + freshen the vault via `run_vault_sync()` (on failure: flag and continue — aggregate what the vault has). **(1)** Target weeks = just-completed ISO week + 3 prior ∪ all completed weeks since last success, cap 12 (over cap → notification instructing `--backfill`); the in-progress week is never written, preserving §1.1.1's invariant (missing row = failure). **(2)** Pure-local vault aggregation — imports `notes.parse_frontmatter`/`daily_path` and `state.read_state` from `_sync` (the parser that wrote all 593 notes is definitionally the correct reader); Days With Data counts notes with ≥1 metric key beyond `{date, source}` (grounded: 2026-08-18.md has only those two); sleep coalesces `sleep_hours ?? sleep_hours_inferred` (Years.md logic); Weight Delta walks back to the most recent prior non-blank week. **(3)** Interactions self-heal *before* counting: empty Date := `created_time`; blank title := `MMM D · Type`. **(3.5)** Offline-capture replay: per-file `pending/<uuid>.json` from the Shortcut's iCloud folder — create with the uuid echoed in the page body (exact dedupe key, so two same-day same-person touches survive), delete that file on success, dead-letter after 3 failed Mondays with one notification. **(4)** Social Touches: one date-range query spanning all target weeks, bucketed locally. **(5)** Upsert: one compound title-equals query, then per-week create-or-update the **full row** — every aggregate rewritten for all trailing weeks so late Sunday-night sleep (D+1 fetch can land after 07:40) and late-logged touches converge within a week; blanks written as explicit nulls. **(6)** People-cache export: one query (~35 rows) → `notion-people.json` (tier-sorted) into the Shortcuts iCloud folder, atomically. **(7)** Watchdog in a finally-block: notify on any step failure, Days-With-Data = 0, vault stale >7 days, or daily-job state >3 days old. Every step is idempotent — a run killed anywhere reconverges next run with zero cleanup. `--backfill 2025-W01`: ~85 throttled creates ≈ 30–60 s, rerunnable.

#### 2.1.4 `scripts/deadman_check.py` (new, ~140 lines) — THE single dead-man switch

One paginated Monthly Money query over a **trailing 6-month window** (fixes fatal #1: the target never advances past an incomplete month — two skipped sittings accumulate named months instead of orphaning one). Pending = any window month (excluding the current one) missing or with blank Net Worth (reading a formula property is §1.10-legal; the guard's `toNumber("")` yields a detectable null). Pending → **one** notification naming all pending months and, for present-but-incomplete rows, the empty balance columns; a month older than ~75 days gets urgent wording (approaching the assumed 90-day bank-export horizon). Max one notification per week — no stacking, no escalation (nag fatigue is the documented abandonment trigger). Export regen on **stamp-map change** (`{month: (net_worth, income, spend)}`): any complete month new or changed → regenerate `exports/monthly_money.csv` in full (atomic tmp+rename — an open Excel never sees a torn file), covering both the sitting-before-first-Friday case and recategorize-only sessions. Also: any `state/import/*.json` with phase ≠ done older than 1h → "import batch incomplete" notification; its own Notion failure notifies *louder* than the nag it replaces.

#### 2.1.5 `scripts/import_transactions.py` + `money/parsers.py` + `money/rules.py` (new) — the money pipeline

Subcommands: `import` (default) · `inspect` · `re-aggregate` · `export` · `recategorize` · `repair-batch`.

**Drops contract:** `drops/YYYY-MM/` (statement month) containing `rbc-chequing.csv` / `rbc-cc.csv` / `scotia-visa.csv` — the 10-second rename-on-save *is* the account+month binding; account is never inferred from content (though the RBC parser cross-checks the Account Type column and aborts on mismatch). Overlapping export ranges are encouraged: hashes dedupe them, and Month derives from Date, so rows route to their correct months regardless of folder.

**Parsers (validation-first — zero real CSVs exist on disk, so every column assumption is marked to-verify):** RBC family (chequing + CC share one format; the 8-column header `Account Type, Account Number, Transaction Date, Cheque Number, Description 1, Description 2, CAD$, USD$` verified verbatim against personal_finance_v2.xlsx's RBC Import sheet); Scotia Visa has two candidate shapes (headerless 3-column portal CSV vs Date|Description|Debit|Credit|Balance) — **`inspect` arbitrates**. First contact per format MUST be `inspect`: prints header/columns/samples/inferred sign (showing a known payroll or purchase row), and on human confirm writes `{fingerprint, date_format, sign_multiplier, confirmed}` into config — **sign conventions are confirmed, never guessed** (the RBC-CC purchase sign is the single most import-breaking unknown). Every subsequent run re-fingerprints before parsing row 1; drift, >2% unparseable rows, populated USD$, or account mismatch → the whole file aborts **before any Notion write**, naming the exact difference. Ported from lighthouse `csv.js`: `parseAmount` (currency symbols, thousands commas, accounting parens), BOM handling, the local-date lesson. Rejected from `bank.js`: heuristic column detection, deposit-discarding, unordered dict rules — each a silent-misparse vector.

**Rules (`config/categories.yml`):** ordered first-match-wins substring rules over the normalized description, with optional account/sign/amount guards; 63-rule seed from the xlsx Keyword Rules sheet remapped to the §1.1.4 taxonomy; `E-TRANSFER IN` (sign-guarded → Income — Other) explicitly ordered **above** `TRANSFER` (a loader unit fixture proves the shadow-rule check against the real seed — ordered wrong, every incoming e-transfer silently vanishes from Income). No match → Uncategorized, never a guess. Loader hard-fails on unknown categories. Promote workflow: fix rows in the Uncategorized view → add a yml line → `recategorize` (touches only currently-Uncategorized rows, so manual fixes are unreachable by construction) → auto-re-aggregate; git history = taxonomy changelog.

**Import internals:** parse (pure, no network) → per-row hash `sha256(account_key|raw_date|raw_amount|raw_description|dup_index)[:16]` with dup_index = ordinal among byte-identical lines in this file → journal `state/import/<batch-id>.json` (batch-id `YYYY-MM-DD·account-key`) → prefetch: per touched month one paginated Month-equals query (2–4 pages) building hash→page-id, unioned with the journal **and, on resume, an Import-Batch-equals query for the crashed batch** (fatal #2's residue closure) → write queue: absent → **one create call carrying all properties incl. Hash + Import Batch** (hash never patched after — this is what makes crash-resume safe) plus a children paragraph holding the verbatim raw line; present → update script-owned fields only if changed, **never touch Category on an existing row**, never delete; **journal flushed after every create ack** (≤3 tiny atomic local writes/sec — cost nil; never journaled before the ack, which would silently drop a row) → re-aggregate each touched month from a **fresh post-write Notion query** (never parse sums) → Monthly Money upsert (script-owned fields only; >1 row for a month → loud failure) → gated export → sidecars (`.imported-<key>.json` with the file's sha256) + summary printout (rows created/skipped/updated, Uncategorized count, per-month Income/Spend, warnings — incl. |Σ Transfer — CC Payment| > $200 mismatch and any |amount| > $50,000 interactive confirm). **Resume at every step**: mid-parse → nothing written; mid-create → prefetch ∪ journal ∪ batch query mark landed rows as skips; before re-aggregation → re-run is all-skips-then-aggregate (the deadman independently notices a stale journal at 1h); mid-export → pure local rewrite. `repair-batch <id> --list/--delete`: archive a bad batch to Notion trash (30-day recoverable), drop the sidecar, auto-re-aggregate — ~5 min, no row surgery.

#### 2.1.6 `lib/` — one shared implementation (one Phase 3 line item)

`notion_api.py` (~120 lines over `requests`, no SDK): token-bucket ≤3 req/s; 429 honors Retry-After (else exponential 1/2/4…60 s, max 5); 502/503/504/connection retried once; 400/401/403/404 **never** retried — immediate loud abort (401 names the rotation runbook; 400 validation errors surface the property name). Write failures abort the run — a skipped ledger write is a broken invariant (unlike `garmin_io`'s skip-and-continue, which is right for health metrics and wrong for money). `notify.py`: osascript notification, always mirrored to the log, per-run dedupe. `weeks.py`: ISO-week math so all scripts agree by construction. `fsio.py`: atomic tmp+rename JSON writes (ported from lighthouse `io.js`) for **all** new state/journals/sidecars/stamps/exports — deliberately replacing `_sync/state.py`'s non-atomic pattern for new code.

#### 2.1.7 `launchd/install.sh` + three plists

Preflight = `_sync/doctor.py` verbatim. Then: **fire a test notification and require human y/n confirmation before bootstrapping anything**; copy plists (`StandardOut/ErrorPath → ~/Library/Logs/notion-os/`, Console-visible); bootstrap + kickstart each; then **assert effects, not exit codes** (TCC can deny a launchd python what Terminal was granted): today's daily note mtime advanced, `notion-people.json` written in the Shortcuts container, deadman state stamped — failures name the Full Disk Access fix. `--doctor` re-runs all asserts and rotates oversized logs.

#### 2.1.8 iOS Shortcut "Touch" (built on-device, ~1h)

Reads `notion-people.json` from the Shortcuts iCloud folder (cached locally by iCloud — the menu works offline) → Choose from List (tier-A first; a trailing "Options…" submenu covers Group/Call/Async so the modal 1:1 path costs zero extra taps) → POST `/v1/pages` with the **capture token**: People relation + Type + Date = now; title deliberately omitted (the weekly heal names it); children = one `capture-uuid: <uuid>` paragraph (the replay dedupe key). Offline or non-200 → save `pending/<uuid>.json` + "Saved offline — syncs Monday". Verify-first on-device at the build weekend: both capture paths timed per §1.4, title-omitted create, and Mac-side launchd readability of the Shortcuts container — **committed fallbacks exist for both risky bits** (manually-pasted dictionary menu; Notion-app offline path).

### 2.2 The per-sync table

| Sync | Direction | Frequency | Trigger | Requests/run |
|---|---|---|---|---|
| garmin-vault-daily | Garmin API → vault markdown (Notion: zero) | Daily 07:15 | launchd → `garmin_daily.py` (also step 0 of every rollup, same lock) | Garmin ~19–20 typical; catch-up ≈ 6N+1 |
| weekly-health-rollup | vault → Weekly Log; Interactions self-heal + replay | Monday 07:40 | launchd → `weekly_rollup.py` | Notion ~9–17; backfill once ~90 |
| people-cache | People DB → iCloud JSON → Shortcut menu | Weekly (rollup step 6) | in-process | 1 query + 1 atomic file write |
| ios-capture | Phone → Interactions create | Event-driven (~4–10/wk) | Action Button / widget | 1 POST (0 when offline-queued) |
| monthly-transaction-import | drops/ CSVs → Transactions + Monthly Money | Monthly sitting, days 1–5 | **Manual**, nagged by deadman | ~270–430 ≈ 2–4 min at ≤3 req/s |
| deadman-monthly-watch | Monthly Money → notification (+ export regen) | Friday 09:00 | launchd → `deadman_check.py` | 1–2 reads (+1–2 on regen); 0 writes ever |
| gated-excel-export | Monthly Money → `exports/monthly_money.csv` → workbook | On import / on stamp change / on demand | import final step; deadman; `export` | 1–2 reads |

**Failure modes and the skipped-two-weeks story, per sync** (detection → behavior → recovery):

**garmin-vault-daily.** *Auth death* (credential/lockout/MFA/SSO — the 87-day killer): classified on the stderr substring set → immediate runbook notification, `auth_dead` stops retries → `--reauth` once; gap self-fills. *Outage/429/network*: per-endpoint isolation, quiet ≤2, notify on 3rd consecutive → next run's lookback re-fetches; Garmin retains data server-side. *Mac asleep/off*: runs on wake; login catch-up via RunAtLoad+debounce; gap >14 auto-handled by `--since`. *Job dead (plist/TCC)*: the rollup's daily-job-stale check screams within 3–7 days (previously invisible — rollup step 0 kept the vault fresh, masking a dead daily job forever). *Weight payload shape wrong*: extractor returns `{}`/nulls with a warning — blank columns, never garbage; the discovery probe on scale day is the gate. **Skipped 2 weeks:** vault freezes exactly like May 2026 — but detection fires at day 3 and day 7, not day 87; revival = one wrapper run (`--since` rewrites every missed note, bodies preserved) + one rollup run, zero manual steps unless auth also died.

**weekly-health-rollup.** *Notion 401/404*: fails before writing, notification names the runbook; vault still freshened. *Schema drift*: 400 surfaces the property name; drift is a bug (§1 is confirmed) — rename back, rerun. *Killed mid-run*: partial trailing rows are harmless — full-row title-keyed upserts; next run rewrites the identical window, zero cleanup. *Vault stale/empty*: the row is **still written** (Days With Data = 0 — §1.1.1: a missing row must always mean script failure) plus notifications. *Poison replay entry*: retried ≤3 Mondays → dead-letter + one notification. *Late-arriving data*: by design — the whole trailing-4 window rewrites weekly. **Skipped 2 weeks:** two missing Monday rows (the human-visible alarm) + the meta-watchdog at day 9; on revival one run enumerates both weeks, recounts every touch logged during the outage (2 < 4-week window), heals the backlog, replays the queue, refreshes the cache. Fully self-healing by construction.

**people-cache.** *iCloud lag/TCC*: degradation is "menu missing this week's new people," never a broken capture; install asserts this exact write. *Person renamed/archived*: page IDs are stable — a rename still posts to the right person; an archived person's capture 404s into the offline queue and dead-letters with notification. **Skipped 2 weeks:** stale snapshot; new people captured via the app path; converges instantly on next export (full overwrite, no incremental state).

**ios-capture.** *Offline/non-200*: per-capture file + "Saved offline — syncs Monday"; capture stays <10s. *Capture token dead*: 401 → captures queue as files and **lose nothing** — replay uses the Mac token (the two-integration split at work). *Human stops capturing* (the real risk — behavioral): Social Touches honestly reads 0 and the Due view fills — the designed nag; backdated entries heal and recount exactly. **Skipped 2 weeks:** benign in both senses — either honest zeros, or unreplayed files that the first revival rollup names, dates, replays, and recounts in one pass. No scenario loses a captured touch.

**monthly-transaction-import.** *Format drift/unconfirmed format*: whole-file abort before any write, naming the difference → `inspect`, confirm, re-run. *Wrong sign convention*: visibly wrong totals + CC-payment mismatch warning → `repair-batch --delete`, fix via `inspect`, re-import (~5 min). *Killed mid-create*: hash-in-create + per-ack journal + batch-id resume query → re-run converges from any death point; the deadman notices a stale journal at 1h. *API down/429s*: loud abort mid-queue (money writes never skip-and-continue); journal preserves progress. *Duplicate rows from bank description reformatting*: both hash variants persist (stability beats cleverness) → visible doubled totals; delete by hand or repair-batch, keep overlap windows short. **Skipped 2 weeks:** the sitting slides — nothing breaks; the deadman nags every Friday naming every pending month; Net Worth stays blank (the design signal, not damage); a 6-week export window is fine (hashes dedupe, Month keys route, multi-month re-aggregation recomputes). Only cost: lateness of THE number, and the export-horizon risk the nag flags at ~75 days.

**deadman-monthly-watch.** *The deadman itself dies*: the daily job's meta-watchdog flags it at day 9; the import prints the stamp's age (warn >10 days) as the human-loop backstop; the blank Net Worth cell in the Ledger view remains the passive §1.3 signal. *Two sittings skipped*: both months stay pending in the window — one notification names them all. *Balance typo (false all-clear)*: out of scope by design — the switch checks completeness, not correctness; a later fix re-triggers the stamp compare. **Skipped 2 weeks:** two missed nags, flagged at day 9; state is per-month counters + a stamp map, so revival re-evaluates current truth over the whole window — a skip spanning a month boundary *adds* the new month to pending rather than replacing the old one.

**gated-excel-export.** *Month incomplete*: row skipped, never zero-filled — Excel never ingests a plausibly-wrong number; regenerates the week the six balances land. *Past month changes after export*: full-file rewrite on the next trigger — the CSV can never diverge from Notion for longer than a week. *Workbook link rot*: visible #REF!, fixed-path contract, one external reference to re-point. **Skipped 2 weeks:** at most one completed month behind, and only if both triggers failed; a pure function of Notion state with no memory beyond an optimization stamp — convergence is always one run.

### 2.3 Repo layout, secrets, config

**Two repos, deliberately.** `~/notion-os` (this spec repo) becomes the monorepo for all new code; `Vault/Garmin/_sync` **stays in place** with its own venv, GitHub remote, and history — it ran clean on 2026-08-19, its path model is parent-of-`_sync`, and moving a working writer is pure risk. Cross-repo seams are one-directional and explicit: subprocess `sync.py` via config paths; `sys.path`-import of the pure parser functions.

```
~/notion-os/
  notion-os-spec.md   plan.md (Phase 3)
  config/   config.yml (committed, non-secret: DB ids, paths, pinned Notion-Version,
            pt_type_allowlist, per-account parser profiles w/ fingerprints + sign_multiplier,
            all thresholds)  ·  categories.yml (committed; git history = taxonomy changelog)
  scripts/  garmin_daily.py  weekly_rollup.py  deadman_check.py  import_transactions.py
  money/    parsers.py  rules.py
  lib/      notion_api.py  notify.py  weeks.py  fsio.py
  launchd/  3 plists + install.sh
  state/    (gitignored) job states, locks, import journals, stamps
  drops/    (gitignored, PII) YYYY-MM/<account-key>.csv + .imported sidecars
  exports/  monthly_money.csv (gitignored — the one Notion→Excel artifact)
  logs/     (gitignored) per-run detail files      .venv/  requests, PyYAML, python-dotenv
```

**Secrets** — all under `~/.config/notion-os/` (700/600), never in the vault or either repo: `garmin.env` (moved out of the Obsidian-synced vault — the §0.10 exposure closed); `notion.env` for internal integration **notion-os-mac** (all 5 DBs); a second integration **notion-os-capture** shared *only* to Interactions + People, its token living solely inside the Shortcut. Two tokens by design: the lock-screen device's blast radius excludes all money data; either rotates without touching the other; a phone-token death loses zero captures. Build-weekend sweep also deletes the expired Google `credentials.json`/`token.json` from `~/Downloads/mission-control/scripts/`.

### 2.4 Reuse map (grounded line-by-line; honest not-reused list)

- **Reused untouched:** `_sync/state.py`, `garmin_io.py` (fetch: backoff/retry/404 policy), `notes.py` (body-preserving writes; `parse_frontmatter` imported as the corpus reader), `sync.py`'s CLI/gap logic (14-day cap, 2-day lookback, 90-day max), `doctor.py` (install preflight, verbatim), `discovery.py` probe pattern, all CLAUDE.md dragons as constraints.
- **Adapted (3 files, 3 commits to `_sync`):** extractors + sync fetch entry + auth env path, per §2.1.1.
- **Ported (lighthouse, wrong language to import):** `csv.js` parseAmount/BOM/date lessons → `money/parsers.py`; `io.js` atomic writeJSON → `lib/fsio.py`.
- **Pattern-only:** `bank.js` drops-folder intake + per-file accounting + digit-scrub (Notion titles only, never hash input); `garmin_io`'s isolation shape → `notion_api.py` (money's stricter error taxonomy adopted verbatim); Years.md inferred-sleep fallback → one-line coalesce; personal_finance_v2.xlsx as **data** (63 Keyword Rules → seed; RBC/Scotia sheets document the assumed formats).
- **Explicitly rejected from salvage:** `bank.js` heuristic column detection, deposit-discarding spend-only extraction, unordered dict categorization (silent-misparse vectors, all three); `_sync/state.py`'s non-atomic writes for new code.
- **Not reused, honestly: Mission Control — nothing for v1.** v1 has zero Google surface; `auth.js`/`setup-auth.js` are googleapis OAuth plumbing with no consumer (Notion auth is a static bearer — nothing to attach a refresh flow to); the inbox/calendar scripts are Gmail/GCal domain logic with no CSV, no queue, no upsert worth extracting; token expired 2026-04-25, consent screen in Testing mode. Reserved as the v2 email/calendar starting point only if that deferral unfreezes *and* the OAuth app gets published. Also not reused: `infer_sleep.py` (fields consumed, code retired), the five Dataview dashboards, the rest of lighthouse.

### 2.5 Runbooks (README material; the spec records them so Phase 3 just copies)

1. **Garmin token death** — immediate notification (auth skips the 3-strike grace). Lockout wording → wait ~1h. Password changed → edit `garmin.env`. Then `sync.py --reauth`; MFA mention → check Garmin settings (MFA is deliberately off). `auth_dead` self-clears; the gap self-fills; the next rollup repairs Weekly Log. No further action.
2. **Notion token rotation** — Mac token: regenerate → paste into `notion.env` → `weekly_rollup.py --dry-run`. Capture token: regenerate → paste into the Shortcut's Text action → test one capture. Independent by design; queued captures survive a phone-token death.
3. **CSV format drift** — the import already aborted before any write, naming the exact difference. `inspect` the new export → confirm (re-fingerprints, re-derives sign, archives old fingerprint) → re-run. No cleanup exists because nothing partial ever landed.
4. **Machine off a month** — nothing fires while off; at next login RunAtLoad fires all three jobs, debounced to one run each: sync `--since` rewrites every missed note; rollup writes ≤12 missed weeks + heals + replays + refreshes; deadman names every pending month in one Friday nag. Human actions: possibly one `--reauth`, one money sitting. Verify with `install.sh --doctor`.
5. **Shortcut field failure** — offline → queued file + "syncs Monday" (do nothing); cache missing → app-path fallback, self-repairs next rollup; 401 → rotate capture token (captures queue meanwhile); repeated replay failure → dead-letter + one notification with contents.
6. **Bad-import repair** — `repair-batch <id> --list` → `--delete` (Notion trash, 30-day recoverable, auto-re-aggregates) → fix cause (`inspect` for signs; rename for wrong account) → re-import → 30-second spot-check. Hand-fixed categories on other batches untouched.
7. **The monthly sitting itself** (~15 min): Friday nag → export 3 CSVs into `drops/<YYYY-MM>/` under the contract names (the rename is the binding) → `import` → read the summary → fix Uncategorized (promote recurring merchants to yml) → type the six numbers into the month's row → Net Worth appears, nag self-clears, export regenerates by next Friday. First run: `inspect` each real export first — column assumptions and sign conventions are confirmed there, never guessed.

### 2.6 Decision log (contested points; every red-team finding adopted)

| # | Point | Decision |
|---|---|---|
| F1 | Deadman target month (fatal) | Trailing 6-month window; per-month self-clearing counters; oldest-month-first export runbook; ~75-day urgency wording. |
| F2 | Import journal cadence (fatal) | Flush after **every** create ack; never journal before the ack (would silently drop a row); resume unions an Import-Batch query. |
| M3 | Garmin auth detection | Substring classification set + `auth_dead` stop-retrying flag; immediate notification. |
| M4 | Watchdog symmetry | Weekly job watches the daily job (one stat call) — closes the only silent-death hole. |
| M5 | Notification channel trust | Human-confirmed test notification gates install; every notify mirrored to log. |
| M6 | Coalesced-wake double sync | One shared blocking flock around every `sync.py` invocation + freshness skip (verified body-loss race in `notes.write_daily`). |
| M7 | Dead-man double-spec | ONE deadman: health's naming/plist/state, money's superset internals, Friday 09:00; the second variant deleted (double-nagging = nag fatigue = the abandonment trigger). |
| M8 | Secrets/token architecture | `~/.config/notion-os/{garmin.env, notion.env}`; two Notion integrations (mac = all DBs; capture = Interactions+People only). |
| M9 | Repo layout double-spec | One ratified tree (entrypoints in `scripts/`, modules in `money/`+`lib/`); launchd logs → `~/Library/Logs/notion-os/`; `_sync` stays in the vault. |
| m10–17 | Minors | Per-file offline queue with uuid-body dedupe + dead-letter; RunAtLoad + debounce (erases the powered-off starvation corner); episode-deduped meta-watchdog; 63-rule seed with the E-TRANSFER-IN ordering fixture; stamp-map export regen (nag-history gate deleted); assert-effects install/doctor (TCC); `--since`-only catch-up chooser (`--days` excludes today — verified). |
| — | Vault sync cadence | **Daily**, not weekly: gap safety vs the 14-day cap, D+1 sleep convergence, watchdog sharpness, prompt weigh-ins; ~20 Garmin calls/day is trivial. |
| — | launchd topology | Exactly three plists, one per cadence, internally chained (launchd has no dependency graph; merging the deadman into the rollup would silence the money nag whenever health breaks). |
| — | Weekly Log write scope | Full-row rewrite of all 4 trailing weeks; §1.1.1's call estimate amended to ~9–17 (honesty over narrowing the design to fit the estimate). |
| — | Invariants restated for Phase 3 | Hash + Import Batch ride in the one create call; Category written once and never again by any script path except recategorize-on-Uncategorized; Bal ×5/Liabilities never script-written; aggregates always from post-write Notion queries; fail loudly or not at all. |

### 2.7 Open questions for the Phase 2 checkpoint

1. **Notification cadence**: daily Garmin failures stay quiet for 2 consecutive and notify on the 3rd (auth failures always immediate). Prefer that grace period, or notify on every failure?
2. **Scotia Visa export**: does your Scotia portal offer a direct CSV export for the Visa, or is it PDF-only (which adds a PDF→CSV conversion step to the monthly runbook)? Only you can see the portal.
3. **Bank export reach**: how far back do RBC and Scotia exports go? We assume ≥90 days (the deadman warns at ~75); if less, the tolerance for slid sittings shrinks.
4. **categories.yml seed review** (~5 min, can wait for the build weekend): CINEPLEX/TICKETMASTER → Misc or a tracked category? SHAW/TELUS/ROGERS → Subscriptions or Housing? Which brokerages do you actually hold (WEALTHSIMPLE/QUESTRADE map to Contribution — Taxable by default)? SHOPPERS/LONDON DRUGS as Health?
5. **Schedule fit**: daily 07:15 / Monday 07:40 / Friday 09:00, all run-on-wake. Does Friday morning suit the weekend sitting, and is your Mac generally asleep-not-shut-down most mornings? (If you routinely shut down for days, everything still converges at next login — nags just arrive later.)

**STOP — Phase 2 complete. Awaiting your confirmation (and §2.7 answers) before Phase 3 (build plan → `plan.md`).**
