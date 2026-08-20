# Notion Life OS v2 — Spec

**Status: Phase 0 complete — awaiting confirmation before Phase 1 (schema design).**

- Phase 0 — Inventory: **this document, below**
- Phase 1 — Schema design: not started
- Phase 2 — Sync architecture: not started
- Phase 3 — Build plan (`plan.md`): not started

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

**STOP — Phase 0 complete. Awaiting your confirmation of what's dead and answers to §0.13 before designing schemas.**
