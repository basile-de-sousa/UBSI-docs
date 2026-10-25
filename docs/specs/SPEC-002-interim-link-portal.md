# SPEC-002: Interim public link portal

status: ready

Review: requested and approved by the project owner on 2026-10-25 (urgent need, implemented the same day)

Created: 2026-10-25

Decision: [ADR-010](../adr/010-interim-link-portal.md)

## Purpose

Until the private portal of SPEC-001 is hosted, give the 46 UBSI members one public page that lists the links they need (Excel exports, Google Sheets, diagrams, Notion, deliverables). The urbanists alone maintain it, and adding or removing a link must take one small edit.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | One static page, published on GitHub Pages from `main`, readable without any account. |
| R-02 | Links live in `site/liens.yml`, grouped by section. A link has a name, and optionally a URL, description, teams, status and last-update date. |
| R-03 | A link without URL is shown as "à venir". Statuses `brouillon` and `obsolete` are visibly flagged. |
| R-04 | Teams use the codes of `data/applications.csv`. Readers can filter by team (remembered in their browser) and search by text. A link without teams concerns everyone. |
| R-05 | A malformed file fails the build; the previously deployed page stays online. |
| R-06 | No document containing personal data is linked (the page is public). Linked Google files keep their own sharing rules. |
| R-07 | Maintenance happens by editing `site/liens.yml` on GitHub and committing to `main`. Only the urbanists (repository writers) can do it. |

## Out of scope

Accounts, file hosting or previews, editing from the page, analytics. These belong to SPEC-001.

## End of life

When the SPEC-001 portal is in production, the page is replaced by a redirect to it and this spec becomes `superseded`.
