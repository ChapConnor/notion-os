# notion-os

The Notion Life OS v1 monorepo. Design: `notion-os-spec.md`. Build order:
`plan.md`. Vault Garmin sync lives separately in `Vault/Garmin/_sync/` (its
own repo, deliberately untouched beyond the three §2.1.1 commits).

**Three launchd jobs. Two manual recurrences. Two repos. Zero servers.**
The recurring human obligations are exactly two: the <10-second social
capture and the ~15-minute monthly money sitting. Everything else runs
itself and fails loudly or not at all.

| Cadence | Job | Script |
|---|---|---|
| Daily 07:15 | com.notion-os.garmin-daily | `scripts/garmin_daily.py` |
| Monday 07:40 | com.notion-os.weekly-rollup | `scripts/weekly_rollup.py` |
| Friday 09:00 | com.notion-os.deadman | `scripts/deadman_check.py` |

Secrets: `~/.config/notion-os/{garmin.env, notion.env}` (700/600). The
capture token lives only inside the iOS Shortcut, nowhere on disk.

## Runbooks (§2.5 — every notification points at one of these)

### 1. Garmin token death
Immediate notification (auth skips the 3-strike grace). Lockout wording →
wait ~1h. Password changed → edit `~/.config/notion-os/garmin.env`. Then
`sync.py --reauth`; MFA mention → check Garmin settings (MFA is deliberately
off). The `auth_dead` flag self-clears when `last_sync.json` advances; the
gap self-fills; the next rollup repairs Weekly Log. No further action.

### 2. Notion token rotation
Mac token: regenerate at notion.so/my-integrations → paste into
`~/.config/notion-os/notion.env` → `weekly_rollup.py --dry-run`. Capture
token: regenerate → paste into the Shortcut's Text action → test one
capture. Independent by design; queued captures survive a phone-token death.

### 3. CSV format drift
The import already aborted before any write, naming the exact difference.
`import_transactions.py inspect <file> --account <key>` on the new export →
confirm (re-fingerprints, re-derives sign, archives the old fingerprint) →
re-run the import. No cleanup exists because nothing partial ever landed.

### 4. Machine off a month
Nothing fires while off; at next login RunAtLoad fires all three jobs,
debounced to one run each: sync `--since` rewrites every missed note; the
rollup writes ≤12 missed weeks + heals + replays + refreshes the cache; the
deadman names every pending month in one Friday nag. Human actions: possibly
one `--reauth`, one money sitting. Verify with `install.sh --doctor`.

### 5. Shortcut field failure
Offline → queued file + "syncs Monday" (do nothing). Cache missing →
app-path fallback, self-repairs next rollup. 401 → rotate the capture token
(captures queue meanwhile). Repeated replay failure → dead-letter + one
notification with contents.

### 6. Bad-import repair
`import_transactions.py repair-batch <id> --list` → `--delete` (Notion
trash, 30-day recoverable, auto-re-aggregates) → fix the cause (`inspect`
for signs; rename for wrong account) → re-import → 30-second spot-check.
Hand-fixed categories on other batches are untouched by construction.

### 7. The monthly sitting (~15 min)
Friday nag → export 3 CSVs into `drops/<YYYY-MM>/` under the contract names
`rbc-chequing.csv` / `rbc-cc.csv` / `scotia-visa.csv` (the rename IS the
account binding) → `import_transactions.py import` → read the summary → fix
Uncategorized in the Notion view (promote recurring merchants into
`config/categories.yml`, run `recategorize`) → type the five balances +
Liabilities (explicit 0!) into the month's row → Net Worth appears, the nag
self-clears, the export regenerates by next Friday.
**First run ever:** `inspect` each real export first — column assumptions
and sign conventions are confirmed there, never guessed.
