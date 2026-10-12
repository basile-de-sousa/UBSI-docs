# ADR-004: Select local preview components after M0 qualification

Status: accepted - Date: 2026-10-11

## Context

The owner approved SPEC-001 and requested execution of the first implementation milestone. PLAN-001 proposed local preview components and a CPU embedding model, subject to M0 qualification. The [M0 report](../qualification/M0-technical-qualification.md) records the actual probes, versions, measurements and failed retrieval policies.

## Decision

- Use a pinned local draw.io viewer **and matching stencil bundle**, with restrictive CSP, an opaque sandboxed frame and editing disabled. Validate/sanitize bounded source data before rendering. Preserve the separate upstream code and stencil notices.
- Use PlantUML's MIT distribution with headless Java, SANDBOX and the built-in Smetana engine for the initial database-diagram adapter. Graphviz becomes optional rather than a required deployment dependency. Unsupported diagrams fail visibly; qualify additional engines before enabling them.
- Read Excel saved values with openpyxl and inspect bounded worksheet XML for formula cache states. An empty numeric cache is unavailable; an explicitly saved string cache may be genuinely empty. Never recalculate formulas in the portal.
- Use local PDF.js canvas rendering, Pillow and sanitized CairoSVG-derived PNG previews for the remaining families. Complete private production delivery and parser bounds in M5.
- Keep E5 as a technically feasible CPU candidate. Retain the multilingual reranker as an experiment. Reject both measured score/margin policies as final chatbot behavior because the quality and regression targets were not met.
- Allow M1 foundation work to proceed. Require new independent evaluation, the retained regressions and urbanist-reviewed expected sources before M6 can pass. Do not weaken SPEC-001's answer/abstention or private-source contract.
- Retain the approved file limits. Adopt configurable initial adapter limits from the M0 report (16 million image pixels, 8,000 px per side, 20 s PlantUML timeout, 256 MiB Java heap, 8 MiB expanded draw.io XML per page), with visible failure and real-host qualification.

## Consequences

- The reference worker needs Java and Cairo; Graphviz is no longer mandatory for the qualified initial UML examples.
- draw.io cannot be packaged as a single viewer script while assuming all named stencil assets are available.
- M0 establishes local feasibility, not completion of any authenticated upload/preview/download or chatbot acceptance scenario.
- The proposed 2-vCPU/4-GiB hosting envelope remains unverified. Linux compatibility, combined memory, concurrent load, SMTP, persistent storage and backups still need qualification.
- Additional retrieval work is a known delivery risk for M6. Faster ranking is not evidence of adequate answers, and the reranker's improved V2 score cannot erase its regression failures.
