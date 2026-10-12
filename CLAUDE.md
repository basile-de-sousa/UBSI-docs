# Project rules

Project: UBSI documentation hub, EPITA SIGL enterprise-architecture course project modeling the information system of AirSIGL (fictional airline). Referentials live as CSV in `data/`; other documents in `files/`. Changes within the Release workflow's path scope on `main` publish CSV Excel exports and a zip of `files/`. The private project knowledge portal has an approved functional baseline in SPEC-001 (`ready`, 2026-10-11), following ADR-003, and an implementation plan in PLAN-001. M0 qualification is documented in docs/qualification/ and ADR-004. M1 foundation, M2 private access, M3 revisioned knowledge, M4 backlog/sprints and M5 imported documents are implemented in portal/ with local reports in docs/qualification/; M6 search/chatbot integration is implemented with 30 migrations; business qualification remains open because the owner will supply UBSI questions and expected answers. Reader activation is gated. M7 local engineering acceptance and operational preparation are implemented: isolated PostgreSQL acceptance, concurrency checks, read-only consistency audit, local load measurement, private quiesced backups/fresh-project restores, trusted proxy mapping and a provider runbook. Final acceptance remains open for M6 business questions, representative private sources, assistive-technology review and real-host email/TLS/off-host recovery/performance. M3 includes 22 migrations, publication services, immutable history, a bounded visual editor, one-time directory import and transactional lexical passages/semantic jobs. M4 extends the schema to 25 migrations, adds typed epic/story publication rules, one active sprint and atomic closure with immutable snapshots. M5 extends the schema to 29 migrations and adds private immutable sources, bounded preview adapters, a leased preview-only worker, current-only file delivery and admin historical originals. M6 adds offline E5/cross-encoder candidate ranking, revision-fenced semantic jobs, current-source links, ephemeral chat and operator-controlled qualification evidence. The hybrid policy is experimental and must not be described as accepted. Both measured retrieval policies failed the quality target and must not be shipped as the final chatbot.

## Commands

- Documentation navigation: `docs/README.md`; as-built decisions: ADR-005 through ADR-009; maintainer reference: `docs/architecture/PORTAL-ARCHITECTURE.md`; French reader/admin workflows: `docs/guides/PORTAL-USAGE.md`. Milestone reports are dated evidence, not a replacement for the consolidated current status.
- Install: `pip install -r requirements.txt`
- Convert CSV to Excel (also the check run in CI): `python scripts/csv_to_xlsx.py`
- Portal setup and environment: see `portal/README.md`; never print or commit `portal/.env`.
- Portal local stack: `docker compose -f portal/compose.yaml up --build -d`
- Portal local SMTP sink: add `-f portal/compose.dev.yaml`; no mail is delivered to real recipients. First admin: `docker compose -f portal/compose.yaml exec web python manage.py bootstrap_admin` (interactive).
- Portal checks: `python portal/manage.py check`, `python portal/manage.py makemigrations --check --dry-run` (load the local environment first).
- Portal read-only operational audit: `python portal/manage.py audit_portal`. Backup/restore/provider handoff: `docs/operations/PORTAL-RUNBOOK.md`. M7 evidence: `docs/qualification/M7-integrated-acceptance-and-operations.md`; reader chatbot activation remains pending business qualification.
- Portal assets: `npm --prefix portal ci --ignore-scripts`, `npm --prefix portal run typecheck`, `npm --prefix portal run build` (Node 24).
- Portal directory import: administration UI, or `python portal/manage.py import_applications --file data/applications.csv --dry-run`; applying requires `--actor UUID` for an active admin. One-time import creates drafts and never overwrites later portal edits; see portal/README.md.

## Rules

- Code, comments, commits, CLAUDE.md, ADRs and specs in English. README.md (the team's entry point) and data values in `data/` are in French.
- Keep it simple. The project owner authorized a custom private website on 2026-10-11 (ADR-003). Complete and approve its specifications before preparing the implementation plan and writing application code. Existing Release outputs remain Excel exports and the zip until an approved implementation changes them.
- `data/` holds tabular data as CSV only; Excel files are generated, never committed.
- The repo is public: never add personal data (emails, Forge logins, student IDs).
- Work directly on `main`: no feature branches, no pull requests. Run the conversion command before pushing.
- A request that is not a bug fix or a trivial change starts as `/spec new` (explore, then draft spec). No code until a spec is `ready`.
- Conventional Commits, with the spec reference when there is one: `feat(data): add flux referential (SPEC-012)`.
- Run the commands above before each commit that touches code. Never weaken a test to make it pass unless the spec changed.
- If a spec, an ADR and the code disagree, stop and report it. Do not resolve it silently.
- Specs and ADRs live in `docs/` and follow the `/spec` skill (formats and workflow).
- If the session-start board lists drafts or proposed ADRs, mention them in one line in your first reply.
