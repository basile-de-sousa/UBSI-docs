# M1 — Application foundation

Date: 2026-10-11

Status: completed locally. Production hosting and remote CI execution are not qualified by this milestone.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md), [ADR-004](../adr/004-m0-preview-and-retrieval-decisions.md).

## Delivered

- An independent Django application in `portal/`, with PostgreSQL as its only configured database engine.
- A custom UUID user in `accounts.0001_initial`, with normalized unique email, display name, active state and reader/admin role. Argon2 is the preferred password hasher. No accounts or credentials are seeded.
- Environment validation with production defaults, database sessions, private filesystem storage outside source/public trees, a restrictive response policy and private-by-default Django views.
- Minimal public liveness/readiness endpoints. Readiness checks database access, migration state, build assets, production static collection and private storage access; operational details are not returned to anonymous clients.
- A French entry page and an explicitly marked, empty development preview of the reader shell. The preview URL is registered only with `PORTAL_ENV=development` and `DEBUG=true`. Unimplemented sections are disabled.
- A pinned Vite/TypeScript/HTMX build, local assets and retained HTMX license. Tiptap and document viewers are not part of M1.
- A multi-stage container running as UID 10001, pinned image digests and a Compose stack with PostgreSQL, a one-shot migration service and web. PostgreSQL and web ports bind only to loopback. Private files and the database use named volumes.
- An isolated portal CI workflow; the existing Release workflow and CSV exporter are unchanged.
- [French setup/operator documentation](../../portal/README.md), an environment template and a local secret initializer that refuses overwrite.

## Completion evidence

| M1 criterion | Observed result | Evidence |
| --- | --- | --- |
| Local setup | Fresh portal virtual environment and locked dependencies installed; Compose created its own network, empty database and private volumes | [Final Compose build/start log](evidence/m1/compose-build.log) |
| Linux build | Python 3.12.14, Node 24.19.0, Django 5.2.17; hashed Python wheels installed and assets built inside Linux ARM64 images | Build log; [dependency provenance](../../portal/THIRD-PARTY.md) |
| Database | PostgreSQL 17.11; 16 framework/custom migrations applied; zero pending migrations and zero seeded accounts | [Runtime observations](evidence/m1/runtime.json) |
| Framework/schema checks | `check`: no issues; `makemigrations --check --dry-run`: no changes; `migrate --check`: exit 0. Commands also completed from native Python against the container database | [Container check output](evidence/m1/django-checks.log) |
| Frontend | `npm ci --ignore-scripts`, `npm run typecheck` and `npm run build` completed natively and in the container build | Build log; exact graph in `portal/package-lock.json` |
| Service state | Liveness and readiness HTTP 200; generic `{"status":"ok"}` response; cache policy `no-store, private`; private directory mode `0700` | Runtime observations |
| Browser shell | Entry-to-preview navigation works. Desktop width 1280 and mobile width 390 have no horizontal document overflow. Mobile menu opens, Escape closes it and returns focus to the toggle; no captured console errors/warnings | [Browser observations](evidence/m1/browser.json), [desktop](evidence/m1/desktop.jpg), [mobile](evidence/m1/mobile.jpg) |
| Existing export | Original command succeeds for applications (10 rows), donnees (0) and flux (0); no changes under `data/`, `files/`, `scripts/` or the Release workflow | [CSV conversion output](evidence/m1/csv-export.log) |

The first build surfaced a missing TypeScript CSS declaration; it was fixed with Vite client types. Simultaneous builds targeting one image name surfaced a Compose image export race; only the web service now builds the shared image. Gunicorn's optional control socket attempted to use an absent home directory; it is explicitly disabled. The final stack starts without that error.

HTMX contains an upstream dynamic-evaluation branch, which triggers a Vite warning. Its runtime configuration disables evaluation, received scripts and inline indicator CSS; the CSP permits neither inline scripts nor `unsafe-eval`. The browser inspection captured no CSP or JavaScript errors. Do not relax the CSP to silence the build warning.

## Scope and remaining work

M1 is the foundation, not the private portal's functional acceptance. Login, invitations, administrator bootstrap, recovery, application role enforcement, throttling and account-management forms remain M2. Revisioned content, the visual editor, sprint behavior, private upload/view/download endpoints, jobs and retrieval remain their planned milestones. No automated domain test suite was added or run in M1; the recorded results are the foundation build/setup checks and UI observations above.

The production environment remains unspecified. HTTPS/proxy configuration, SMTP delivery, real-domain HSTS policy, backups, Linux document-renderer integration and combined model/worker/web resource use must still be qualified. M0's failed retrieval policies remain rejected. A successful Linux foundation build does not qualify the future preview/search stack or the proposed memory envelope.

The new GitHub Actions workflow has been written but not executed on GitHub; these changes have not been pushed. Its Ubuntu AMD64 execution remains to be observed. Source changes stay in the current `main` checkout; existing untracked spreadsheets are untouched.

Local inspection services are stopped after evidence capture without deleting their named volumes. Restart using the documented Compose command.
