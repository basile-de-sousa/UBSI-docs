# Project rules

Project: UBSI documentation hub, EPITA SIGL enterprise-architecture course project modeling the information system of AirSIGL (fictional airline). Referentials live as CSV in `data/`; other documents in `files/`. Each change on `main` publishes a GitHub Release with the CSVs converted to Excel and a zip of `files/`. There is no website.

## Commands

- Install: `pip install -r requirements.txt`
- Convert CSV to Excel (also the check run in CI): `python scripts/csv_to_xlsx.py`

## Rules

- Code, comments, commits, CLAUDE.md, ADRs and specs in English. README.md (the team's entry point) and data values in `data/` are in French.
- Keep it simple: no website, no generated display of the data. The only build output is the Excel export and the zip in the Release.
- `data/` holds tabular data as CSV only; Excel files are generated, never committed.
- The repo is public: never add personal data (emails, Forge logins, student IDs).
- Work directly on `main`: no feature branches, no pull requests. Run the conversion command before pushing.
- A request that is not a bug fix or a trivial change starts as `/spec new` (explore, then draft spec). No code until a spec is `ready`.
- Conventional Commits, with the spec reference when there is one: `feat(data): add flux referential (SPEC-012)`.
- Run the commands above before each commit that touches code. Never weaken a test to make it pass unless the spec changed.
- If a spec, an ADR and the code disagree, stop and report it. Do not resolve it silently.
- Specs and ADRs live in `docs/` and follow the `/spec` skill (formats and workflow).
- If the session-start board lists drafts or proposed ADRs, mention them in one line in your first reply.
