# M6 — Reader search and grounded assistant

Date: 2026-10-12

**Status: integration implemented on `main`; retrieval acceptance pending.** The owner will supply UBSI questions and expected answers for urbanist review. The proposed synthetic qualification set is not approved and was not executed. The reader assistant remains disabled by its qualification gate; general search is available and admins have an explicitly experimental preview. M7 has not started. No automated tests or retrieval acceptance evaluation were added or run in this milestone.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md), [ADR-004](../adr/004-m0-preview-and-retrieval-decisions.md). French operating instructions: [portal README](../../portal/README.md). Proposed review material and intake instructions: [M6 qualification](../../qualification/m6/README.md).

## Delivered

- Authenticated French lexical search over current published knowledge, with reference lookup, application/epic/sprint/type filters and pagination. Drafts, archived records and superseded publications are excluded. Imported file bytes are not part of the chatbot corpus.
- Published FAQ, epic, user-story and specification sections form the assistant corpus. Local multilingual E5 embeddings and a multilingual cross-encoder provide candidate retrieval and reranking. Seventeen pinned model artifacts are SHA-256 verified before loading; inference uses local files on CPU. Native setup, the Linux ARM64 image and the CI configuration acquire the same artifacts. Remote CI was not run.
- Durable semantic jobs use transaction locks, leases, fencing tokens, bounded subprocesses, retries and publication checks. Publication retains immediate lexical availability; semantic retrieval reports technical unavailability while a required current index is missing. Reindexing does not publish content or approve the assistant.
- Responses contain at most one exact source excerpt and its title/reference/section, with a link to the current publication. There is no generated answer text. Signed links and the destination page both check publication identity; replacement and archive invalidate old destinations.
- Unknown or rejected questions receive the exact urbanist fallback. Index/model errors and qualification pending are distinct states. The experimental policy includes adequacy/margin thresholds, explicit-reference checks and limited conflicting-source rejection. These controls have **not** established general retrieval quality or contradiction detection.
- Separate reader and admin interfaces, loading/error/retry states, question bounds, per-account rate limits, five database retrieval slots and a per-process inference lock. Exchanges exist only in page memory, can be cleared, and are not stored as a transcript.
- Operator activation requires a private report matching the implementation/policy fingerprint, approved expectations, separate calibration and held-out groups, retained M0 regressions and passing quality/lifecycle evidence. The web UI cannot approve itself. Changes to the fingerprint invalidate previous approval. The supplied example report cannot activate the assistant.

## Environment and actual state

The existing isolated `ubsi-portal-m2-preview` Compose project and its previously authorized fictional admin/reader accounts were reused. Four dedicated fictional FAQ records were added for publication, conflict and draft-exclusion observations. No real UBSI content or user spreadsheet was imported. Credentials were handled through memory/stdin without password files or credential output.

The isolated database has **30 applied migrations**, **35 records** and **40 published revisions**. The current eligible assistant corpus has **7 records, 11 passages and 11 chunks**, with **7 current indexes**, no pending/failed semantic jobs and no leased retrieval slots. Nine semantic jobs completed and ten superseded jobs remain recorded. Two additional index metadata rows describe historical revisions; current queries exclude them. Ineligible and obsolete current passages both count zero. The five deliberate failed preview jobs from M5 remain unchanged. [Runtime snapshot](evidence/m6/runtime.json), [final index status and fingerprint](evidence/m6/search-status.json).

The normal local development database was migrated separately to 30 migrations and remains empty of accounts, content, files and jobs. [Normal database snapshot](evidence/m6/normal-database.json).

## Manual observations and technical checks

These are scoped engineering observations on fictional data, **not** a scored quality evaluation or the full acceptance matrix.

| Area | Observed result | Evidence |
| --- | --- | --- |
| Packaging/schema | Native Django configuration, migration drift/check and TypeScript checks pass. The final Linux ARM64 image builds and its configuration/schema checks pass | [Checks and image metadata](evidence/m6/checks-build.log) |
| Reader search | `modification` returns the published FAQ and specification; the FAQ filter narrows the result. Application/epic/sprint selectors show readable labels | [Desktop](evidence/m6/search-reader-desktop.jpg), [browser notes](evidence/m6/browser.json) |
| Source response | An exact FAQ question returns its stored excerpt; its link opens the current source | [Admin source card](evidence/m6/assistant-source-admin.jpg) |
| Unknown/conflict/draft | An unrelated weather question falls back; two same-title opposing fictional rules fall back; a draft-only answer is not returned | [Unknown](evidence/m6/assistant-fallback-admin.jpg), [conflict](evidence/m6/assistant-conflict-admin.jpg), browser notes |
| Replacement | After publishing version two, the old link is unavailable. Before indexing, retrieval reports technical unavailability. The container worker processes the new version and its card contains only the new excerpt | [Old link](evidence/m6/stale-link-denied.jpg), [index pending](evidence/m6/index-pending-admin.jpg), [new source](evidence/m6/current-revision-source.jpg), [replacement state](evidence/m6/replacement.json) |
| Archive | Archiving that FAQ invalidates its current source link and removes it from search | [Unavailable link](evidence/m6/archived-link-denied.jpg), [archive state](evidence/m6/archive.json) |
| Reader permissions/gate | Reader admin access is denied; the reader assistant states that qualification is pending and returns no source card | [Admin denial](evidence/m6/reader-admin-denied.jpg), [reader assistant](evidence/m6/assistant-reader-pending.jpg) |
| Page interaction/mobile | Empty input produces a local hint; clearing/navigation remove page exchanges. Search and assistant have measured viewport/page widths of 390px; mobile navigation works. Final browser error logs are empty | [Mobile search](evidence/m6/search-reader-mobile.jpg), [mobile assistant](evidence/m6/assistant-reader-mobile.jpg), browser notes |
| Anonymous access | Health endpoints return 200; private pages redirect to login, assistant APIs return 401, private responses use no-store caching | [HTTP observations](evidence/m6/public-http.json) |

## Corrections and remaining limits

- Initial semantic subprocess attempts failed because the sanitized child host setting lacked the application's required local host. The setting was corrected and the five initial jobs completed on retry. Source text was not included in failure logs.
- The initial native preview inherited development debug mode; subsequent observations use the container with debug disabled, including the generic unavailable-source pages shown here. The final image also includes input validation for malformed Unicode/JSON and distinct invalid-question versus technical-error handling. Those final boundary corrections received build/framework checks, not a repeated full browser matrix.
- The model lock retains the explicit CPU package index; native installation with `uv` requires the documented index strategy. Model artifacts are acquired outside tracked source and bundled into the image. Cold model loading was observed natively, but no warmed latency, throughput or memory acceptance figures are claimed.
- The experimental thresholds are not calibrated against an approved UBSI corpus. The observed opposite-answer example does not establish reliable handling of every conflict, paraphrase or unsupported question.
- Concurrent requests/workers/admin updates, hard crash and lease reclamation, every input boundary, direct SQL corruption, complete keyboard/screen-reader coverage, load limits and real-host backup/restore remain unqualified. Compose resource limits are engineering controls, not measured host sizing. M7 still requires its integrated acceptance work after M6 qualification.

## Qualification handoff

The owner's selected next action is to provide **UBSI questions with expected answers and authoritative source references/sections**, including questions that should receive the urbanist fallback. Urbanist review must identify acceptable destinations before calibration and the separate held-out run. The 60 M0 cases remain available as regressions; the new synthetic proposal is preparation only.

No reader activation report has been produced and no retrieval-quality percentage is announced. The admin preview remains experimental until approved evidence satisfies SPEC-001 and ADR-004.

## Teardown

Owned preview services are stopped without deleting database/private volumes. Owned browser tabs and fictional sessions are closed and the temporary viewport is reset. No deployment, commit or push was performed. Source and documentation remain in the current `main` checkout for review.
