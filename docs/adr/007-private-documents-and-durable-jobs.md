# ADR-007: Preserve private originals and prepare bounded local previews with durable jobs

Status: accepted for implementation - Date: 2026-10-12

## Context

SPEC-001 requires imported diagrams/spreadsheets, in-site previews and exact original downloads. [ADR-004](004-m0-preview-and-retrieval-decisions.md) selected local adapters after feasibility probes. Preparation can fail or outlive an HTTP request, and replacement drafts must not damage a published document.

## Decision

- Store immutable original bytes outside the checkout and public asset roots, with UUID storage keys, recorded size and SHA-256. Keep private persistent storage shared by web/worker. There is no public `MEDIA_URL` or direct static mapping.
- Support eleven source extensions: `.drawio`, validated draw.io `.xml`, `.xlsx`, `.csv`, `.puml`, `.plantuml`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.svg`. Category policy distinguishes data flows, spreadsheets and database diagrams; an extension alone is insufficient validation.
- Enforce bounded upload and parser complexity before publication. Defaults include 20 MiB sources, 50 sheets/pages, 200,000 populated spreadsheet cells, 20,000 rows, 200 columns, 200 MiB expanded input, 16 million raster pixels and 8,000 pixels per side. The settings schema defines configurable bounds; the README documents user-visible limits.
- Use the pinned draw.io viewer and stencil bundle, openpyxl saved-value extraction, local PlantUML MIT/Java SANDBOX/Smetana, local PDF.js, Pillow and sanitized CairoSVG previews. Isolate viewer frames with restrictive CSP; reject external resources and active content. Preserve untouched originals only for authenticated attachment downloads.
- Read cached Excel formula values without recalculation, preserving the distinction between missing cache and an explicitly saved empty string. Label hidden worksheets. Treat unsupported/malformed/over-complex sources as visible errors rather than silently truncating a supposedly complete preview.
- Write files privately before linking metadata. Upload creates a new `FileRevision` and preparation job attached to the draft. Publish only a ready compatible preview; a failed replacement leaves the current reader version untouched. History restoration selects the retained original into a draft and still requires explicit publication.
- Authorize every preview, asset, status and original request. Reader URLs resolve the currently published file only; admin draft/history routes use separate authorization. Verify original integrity before download and refuse missing/corrupt storage rather than serving different bytes.
- Use a PostgreSQL job table without an external broker. Claim work transactionally with expiring leases and unique fencing tokens, execute bounded subprocesses, and accept completion only from the current lease holder. Retry transient failures at most three attempts with backoff; permanent source failures require correction. Workers never publish content.
- Apply the same durable-job principles to semantic indexing, with publication/version checks before committing chunks. A worker crash can cause another attempt after lease expiry; do not promise exactly-once process execution.
- Clean temporary/abandoned storage only through the retention-aware cleanup command. Default to a dry run and preserve every file referenced by a draft or retained publication/history. Never clean a volume concurrently with backup or restoration.

## Alternatives considered

- Public diagram-rendering services or CDN viewers expose private source data or introduce external runtime dependencies.
- Replacing original bytes with a sanitized export would break exact downloads and historical recovery.
- Synchronous rendering in upload requests ties resource-heavy parsers to request timeouts.
- In-memory queues and after-commit-only enqueue callbacks lose durable work after crashes.
- Broker-based queues or object storage may become useful later; the initial deployment has no demonstrated requirement for them.

## Consequences and limits

The image includes Java, Cairo, viewers, stencils and models. Retained original history increases storage consumption; the upload cap does not cap total disk. The private filesystem is not transactionally committed with PostgreSQL, so staged-file cleanup and coordinated backup are required.

Local Linux tests cover the approved families and worker recovery; arbitrary UML engines, macros, Excel recalculation and editing draw.io inside the portal are not implemented. Representative private inputs and real-host combined memory/CPU/storage behavior remain acceptance work.

## Evidence

[M5](../qualification/M5-imported-documents.md), [M6](../qualification/M6-search-and-chatbot.md), [M7](../qualification/M7-integrated-acceptance-and-operations.md). Implementation: `portal/documents/`, `portal/jobs/`, `portal/search/semantic.py` and asset locks. [Third-party provenance](../../portal/THIRD-PARTY.md) records licenses and pinned sources.
