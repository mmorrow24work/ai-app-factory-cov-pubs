# ai-app-factory-cov-pubs

List Coventry pubs with facilities, public and personal ratings, sortable by popularity and postcode proximity, shareable, at https://ai-app-factory-cov-pubs.coldwire.uk/ Built and evolved via the unattended (Lane B) Claude Code pipeline: label an issue `claude-go` and `.github/workflows/claude.yml` implements it, opens a PR, and records the run in `docs/journal.md`.

## Requested by

[@mmorrow24work](https://github.com/mmorrow24work), via [ai-app-factory](https://github.com/mmorrow24work/ai-app-factory).

## Support & Handoff

### Support & feedback

Open an issue, or comment on an existing one:

- Apply the `claude-go` label to have the unattended pipeline attempt a fix.
- Comment `@claude` on an issue or PR to give feedback or direct a change mid-build — e.g. "make the button blue instead," or correcting a misread requirement. This isn't limited to collaborators: the project's own recorded requester (see this README's "Requested by" section) can do this too, authenticated by their GitHub account, not a shared credential. Anyone else's `@claude` comment is acknowledged but not acted on.
- Mention `@mmorrow24work` for anything the pipeline can't or shouldn't handle unattended — design decisions, ambiguous requirements, anything labeled `lane:manual`.

### Taking ownership: fork vs. clone

Two different ways to take this project further, depending on what you want:

**Fork it** if you want to keep it connected to GitHub — its issues, PRs, and (optionally) the same unattended pipeline. GitHub forks do **not** inherit the parent repo's Actions secrets, so `claude-go` stops working on the fork the instant it's created — no separate revoke step needed on the original owner's side. To keep the unattended pipeline running, set up your own `CLAUDE_CODE_OAUTH_TOKEN`/`GH_PAT` secrets on the fork (same `claude setup-token` / `gh secret set` steps documented in the `ai-app-factory` repo's own `README.md`).

**Clone it** if you just want the code, with no continued connection to this repo, its issues, or the pipeline that built it — a plain `git clone`, no fork relationship, no shared history on GitHub's side. Simpler if you're folding this into something else or don't want any of the automation baggage, but note you're on your own from there: no `claude-go`, no `@claude` comments, no link back to the original for anyone to follow.

## Data

Pub data comes from [OpenStreetMap](https://www.openstreetmap.org/copyright) via the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API): every `amenity=pub` node, way and relation inside Coventry's administrative boundary, normalised by `scripts/refresh_pubs.py` into `data/pubs.json` (schema in `data/pubs.schema.json`). It's licensed under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/) — the `attribution` field in `data/pubs.json` (`© OpenStreetMap contributors`) must be shown wherever this data is displayed. A scheduled workflow refreshes the data weekly and opens a PR with the diff.
