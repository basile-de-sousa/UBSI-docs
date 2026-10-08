# ADR-002: Share versioned documents through GitHub Releases, no website
Status: accepted - Date: 2026-10-08

## Context

ADR-001 generated a MkDocs site rendering the CSV referentials as pages. The team does not want to maintain a display layer for spreadsheets. The real need is to share versioned documents efficiently: referentials as Excel, and any other file (PDF, Word, slides).

## Decision

- No website. GitHub's own UI is used to browse, diff and review.
- `data/` keeps tabular data as CSV (diffable in pull requests). `files/` holds every other document. `docs/` keeps specs and ADRs in Markdown.
- On every change to `data/` or `files/` on `main`, a workflow publishes a GitHub Release tagged `vYYYY-MM-DD-HHMM` with: one `.xlsx` per CSV, `UBSI_referentiels.xlsx` (one sheet per CSV) and `UBSI_fichiers.zip` (content of `files/`). Release notes list the files changed since the previous release.
- Stable links point to `releases/latest/download/<file>`; older versions stay on the Releases page.
- No schema or data validation beyond "the CSV converts". On pull requests, CI only runs the conversion.

## Alternatives rejected (and why)

- **MkDocs site (ADR-001)**: too much to maintain for the value it adds.
- **Committing the `.xlsx` files**: binaries in history, no readable diff, and they drift from the CSV.
- **GitHub Pages with a download page**: one more thing to maintain, Releases already give stable links and history.

## Consequences

- Team members download Excel from a fixed link without touching git.
- Each release is an immutable snapshot, handy for deliverables ("the version sent on date X").
- Binaries in `files/` are versioned by git but without readable diffs. Large files (tens of MB) should stay on Drive.
- The converter accepts CSV saved by Excel (`;` separator, UTF-8 BOM), so contributors can edit in a spreadsheet.
