# Build Journal

Per-issue record of the unattended (Lane B) build of this project. One entry per Claude run, appended automatically by `.github/workflows/claude.yml` via `.github/scripts/journal-entry.sh`.

## How this file is written

**Entries are appended by the workflow, not by Claude inside its PR.** This is deliberate: having Claude append a journal entry within each PR means every open PR touches the same file, so almost every one goes `CONFLICTING` the moment any other PR merges — leaving green, auto-merge-enabled PRs sitting unmerged indefinitely. Patching from the workflow after the run sidesteps that entirely: Claude's branches never touch `docs/journal.md`.

## What "Estimated Cost" means

This pipeline authenticates via a **Claude subscription** (OAuth), not pay-per-token API billing. The cost figure is notional — what the run *would* cost at standard list rates — useful as a consistent yardstick for comparing runs, not an actual charge.

---

## Build velocity

Recomputed by `.github/scripts/journal-entry.sh` on every run.

<!-- VELOCITY_START -->
| Metric | Value |
|---|---|
| Issues with recorded metrics | 1 |
| Successful runs | 1 |
| Mean time per issue | 3m 55s |
| Mean turns per issue | 40 |
| Mean output tokens per issue | 23,368 |
| Mean estimated cost per issue | $0.3509 |
<!-- VELOCITY_END -->

---

## Entries

<!-- ENTRIES_START -->
<!-- New entries are appended below this marker, newest last. -->

## 2026-08-19 — Issue #3: M1: Pub data schema, Overpass normaliser, data/pubs.json, and schema tests

- **Result:** success
- **PR:** #17
- **Milestone:** M1: Pub data pipeline
- **Model:** claude-sonnet-5
- **Execution Duration:** 235 seconds
- **Turns:** 40
- **Input Tokens:** 128
- **Output Tokens:** 23368
- **Estimated Cost:** $0.3509 (notional — see above)
- **Run:** https://github.com/mmorrow24work/ai-app-factory-cov-pubs/actions/runs/32284330577
