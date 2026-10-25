# ADR-010: Interim public link portal on GitHub Pages
Status: accepted - Date: 2026-10-25

## Context

The private portal (ADR-003, SPEC-001) is built but not hosted, and its chatbot still awaits business qualification. Meanwhile the teams need a single place to find shared documents now. ADR-002 rejected a GitHub Pages download page as "one more thing to maintain"; the README download table only covers Release exports, not Google Sheets, diagrams or Notion.

## Decision

- Publish a single static page on GitHub Pages (SPEC-002), deployed by `.github/workflows/pages.yml` from `site/`.
- The page is a list of links kept in `site/liens.yml`, validated by `scripts/build_site.py`. It shows no data itself; Excel files stay served by Releases (ADR-002).
- It is interim: once the SPEC-001 portal is in production, it becomes a redirect.

## Alternatives rejected (and why)

- **claude.ai artifact**: viewers need a Claude account; part of the team has none.
- **Notion page**: the team can edit it, but the urbanists want to remain sole maintainers, with history in git.
- **Waiting for the private portal**: hosting is not available yet and the need is urgent.

## Consequences

- Narrows ADR-002's rejection of a Pages download page for the interim period. Releases are unchanged.
- The page is public: only links go there, and linked Google files must have the intended sharing setting.
- One-time setup: Settings > Pages > Source: GitHub Actions.
