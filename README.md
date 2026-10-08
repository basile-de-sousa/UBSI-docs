# UBSI docs

Single source of documentation for UBSI, the EPITA SIGL enterprise-architecture project that models the information system of AirSIGL, a fictional airline.

Site: https://basile-de-sousa.github.io/ubsi-docs/

## Layout: data and site are separate

```
data/        Source of truth. One CSV per referential + schema.yaml
docs/        Written content (Markdown): specs, ADRs, guides
site/        Presentation only: theme overrides + hook that renders data/ into pages
scripts/     Data loader and validator (used by CI and by the site hook)
mkdocs.yml   Site config
```

- Data is **never** written in `docs/` or `site/`. Pages for referentials and applications are generated at build time from `data/` and never committed.
- Office files (slides, Word deliverables, PDF exports) stay on the project's Google Drive.
- The repo is public: no personal data (emails, Forge logins, IDs) in `data/`.

## Commands

```bash
pip install -r requirements.txt
python scripts/validate.py   # check data/ against data/schema.yaml
mkdocs serve                 # local preview at http://127.0.0.1:8000
mkdocs build --strict        # build the site into public/
```

CI runs the validator and a strict build on every pull request, and deploys to GitHub Pages on `main`.

## Workflow

Every change goes through a pull request. Specs (`docs/specs/`) and ADRs (`docs/adr/`) follow the `/spec` workflow: plan in chat with `/spec new` and `/spec review`, implement with `/spec run` in Claude Code. See [ADR-001](docs/adr/001-data-and-site-separation.md) for why the repo is organized this way, and [docs/contribuer.md](docs/contribuer.md) for the contributor guide (French).
