# ADR-001: Data as CSV in the repo, documentation site generated from it
Status: superseded by ADR-002 - Date: 2026-10-08

## Context

Team documentation (flux, referential data, sprint specs) was spread across Excel files on Google Drive, Notion pages and loose `.md` files. Nothing was centralized and Excel files could not be versioned in a reviewable way. A git repo inside a synced Google Drive folder was considered and dropped: Drive sync corrupts `.git` and brings none of the review benefits.

## Decision

- `data/` holds the referentials as **CSV files**, described by `data/schema.yaml` (columns, required fields, allowed values, references between datasets). It is the single source of truth.
- `docs/` holds written content only (specs, ADRs, guides), in Markdown.
- `site/` holds presentation only (theme overrides, the MkDocs hook that renders `data/` into pages). It never contains data.
- The site is built with **MkDocs Material**. Data pages and per-application pages are generated at build time and never committed.
- `scripts/validate.py` checks the data. CI runs it and `mkdocs build --strict` on every pull request, and deploys to GitHub Pages on `main`.
- Applications are referenced by a short code (`PLA`, `BKG`...). The codes in `data/applications.csv` are a first proposal.

## Alternatives rejected (and why)

- **Git repo inside Google Drive**: concurrent sync corrupts the repository.
- **Keep Excel as the source**: `.xlsx` is binary, git cannot show what changed in a pull request.
- **JSON or YAML for data**: harder to edit in a spreadsheet for non-developers than CSV.
- **Hand-written data pages**: duplicates the data and drifts out of sync.

## Consequences

- Every change to a referential is reviewed in a pull request with a readable diff.
- Contributors edit CSV, not Excel. An Excel export can be generated from `data/` later if a deliverable needs one.
- itlivemaps.com expects its own Excel layout: feeding it from `data/` needs an export script (not done yet).
- The repo is public, so the site is public: no personal data (emails, Forge logins, IDs) goes into `data/`.
