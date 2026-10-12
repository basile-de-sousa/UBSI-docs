# M3 — Revisioned knowledge core

Date: 2026-10-12

Status: implemented and observed locally on `main`. This checkpoint covers applications, specification pages, FAQ and their shared publication lifecycle. Integrated acceptance and production operation remain M7 work.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md). French usage and import commands: [portal README](../../portal/README.md).

## Delivered

- Stable UUID records and unique non-reused references; separate mutable drafts and immutable published revisions. Current publication pointers, publication state, revision sequence and edit versions are explicit fields.
- Typed draft/revision relationships are foreign keys rather than UUID arrays inside editor JSON. Published relation labels are preserved in history. Reader links resolve current published targets and current published incoming sources.
- Transactional create, begin-edit, save, publish, archive, restore and draft-discard services. Fresh administrator authorization and account-control locking precede the shared project lock. Expected edit versions reject stale writes; creation/publication retries do not create duplicate records/revisions.
- Publication validates the complete payload and all linked published targets before switching the current pointer. Editing or restoring a draft leaves the current publication unchanged. Archiving a required parent with published dependents is rejected.
- PostgreSQL triggers protect published revisions/relations from update/delete and prevent changing record identity or pointing to another record's revision. Model-level protections also reject history edits.
- French admin directory, draft counts/filters, forms, reader preview, explicit publication, history, restoration and archive/discard confirmation screens. Conflict pages retain submitted fields and link to the current editor in a separate tab.
- One-time application CSV preview/import, UI and management command: bounded UTF-8 CSV, signed expiring confirmation, draft creation only, existing code reservations preserved, completion receipt, no subsequent synchronization or overwrite. Publishing an application-code rename reserves the new code and retains the previous codes with the same UUID.
- Locally bundled Tiptap 3.31.3 editor: headings, lists, bold/italic, links, simple tables, row/column controls, plain code, undo/redo. Stable heading UUIDs survive a title change. A missing section displays a notice on the current page.
- One bounded server schema canonicalizes editor JSON and derives escaped HTML, exact text and section passages. No arbitrary HTML, inline styles, remote editor scripts or relaxed CSP. Document/table limits are documented in the usage guide.
- FAQ question/answer, alternative formulations, category, application links and associated contents. Reader lists offer published-text search, application/category filters and pagination; only current published records are eligible.
- Publication replaces lexical passages and inserts a durable semantic-index job in the same database transaction. Archive withdraws passages immediately. Superseded pending jobs remain marked as superseded. Semantic execution and the chatbot remain M6 work.
- Readiness now includes all generated frontend chunks, including the lazily loaded editor. Browser dependency notices include Tiptap/ProseMirror as well as HTMX.

## Environment and evidence

The existing isolated Compose project `ubsi-portal-m2-preview` was reused with its two authorized fictional accounts. Only synthetic content and the public repository application CSV were entered. Credentials remained session memory and were passed through terminal stdin for equivalent rotation; roles and recipients were unchanged. No credentials or real project accounts are included in evidence.

The isolated database contains 22 applied migrations, 13 records, 7 published revisions and 10 working drafts (including a draft of one published record). Four records are currently published: two applications, one specification and one FAQ. The source import receipt has ten rows. Six lexical passages point to current revisions; zero point to an older revision. Two semantic jobs are pending and two superseded, with no worker running. These are fixture counts, not initial production data. [Runtime snapshot](evidence/m3/runtime.json).

| Area | Observed result | Evidence |
| --- | --- | --- |
| Framework and build | Django check reports no issues; no model/migration drift; migration check succeeds. Native TypeScript/build/static collection and Linux ARM64 image build complete. Existing CSV conversion still produces 10/0/0 rows | [Django](evidence/m3/django-checks.log), [frontend/export](evidence/m3/frontend-export.log), [container](evidence/m3/container-checks.log) |
| Service boundaries | Liveness/readiness return 200. Anonymous application/specification/FAQ/admin requests redirect to the clean login URL; private/no-store and restrictive CSP headers remain present | [HTTP observations](evidence/m3/public-http.json) |
| Import | UI preview shows ten applications; confirmation creates ten private drafts. Reader application list is empty before publication. Repeating the command after a portal edit reports an already completed import and preserves the changed code/description | [Import preview](evidence/m3/import-preview.jpg), runtime and browser observations |
| Editor and publication | A specification linked to two published applications saves and publishes with heading/list/table/code/link structures intact. Editing its heading preserves `section-8e0c4c84-3c0c-498d-b5de-cd4c9d86999c`; the reader retains revision 1 until revision 2 is explicitly published | [Editor desktop](evidence/m3/editor-desktop.jpg), [reader desktop](evidence/m3/reader-desktop.jpg) |
| Stale form | Two tabs opened the same working version. The first save succeeds; the second receives a conflict with its submitted title/body still present and the publish button disabled | [Conflict](evidence/m3/stale-conflict.jpg), [recoverable synthetic input](evidence/m3/synthetic-stale-input.json) |
| Restoration | Revision 1 is restored to a new working draft while readers retain revision 2. History remains accessible to the admin. Republishing the restored draft later creates revision 3 | Browser observations and runtime |
| Validation recovery | Empty specification publication fails without removing its draft. The form then successfully saves a correction from the refusal page. Publication with a draft-only application still fails; admin preview shows the saved text but hides the private target | [Blocked publication](evidence/m3/publication-blocked.jpg), browser observations |
| Archive | Archiving the application required by the published specification is refused. Archiving the specification succeeds, makes its reader URL unavailable, and retains its history/draft. Publishing the restored draft makes it visible again | Browser observations and final revision sequence |
| Identity and relations | Publishing `BIL` → `BIL2` retains the application UUID and reciprocal specification/FAQ links. Both codes remain reserved. Reimport does not revert the new description | Runtime snapshot and browser observations |
| FAQ | Question, answer, category, two alternate formulations, application and support links publish. Searching the list for an alternate formulation returns the question | [FAQ mobile](evidence/m3/faq-mobile.jpg), browser observations |
| Reader permissions | Reader navigation omits admin controls. Direct historical revision and admin draft-preview requests show access refusal; a never-published specification's reader URL is unavailable. The published list excludes that draft | Browser observations |
| Responsive UI | Reader specification, FAQ and admin editor observed at 390 pixels with document width 390; reader/editor also captured at 1280. Mobile menu opens/closes. Table column addition and undo preserve rectangular structure; mobile save succeeds. Final editor/reader console captures are empty | [Reader mobile](evidence/m3/reader-mobile.jpg), [editor mobile](evidence/m3/editor-mobile.jpg), [draft directory](evidence/m3/admin-drafts.jpg) |
| Search bookkeeping | Final passages belong only to current revisions; older pending semantic jobs are superseded after publication/archive. The singleton generation reaches 8 for the observed transitions | Runtime snapshot |

The synthetic stale input is an explicitly selected title/body/application snapshot, without cookies, CSRF fields or credentials. Screenshots contain only fictional identities and sample content. [Browser observation notes](evidence/m3/browser.json) describe the manual sequence.

## Corrections made during observation

- PostgreSQL rejected locking a nullable outer-joined current revision on the first application publication. The record query now uses `select_for_update(of=("self",))`; subsequent application and specification publication succeeds while the shared project lock protects transitions.
- The editor form initially posted to the current URL after a publication refusal, which retried publication instead of saving corrected text. Forms now explicitly target the create/edit route. The refusal → correction → save → linked-target refusal sequence was observed after rebuilding.
- With injected editor CSS disabled for CSP, ProseMirror reported a missing `white-space` setting. Local CSS now supplies `pre-wrap`; the final editor console capture is empty.
- A specification form's grid initially inherited the table's intrinsic width on mobile. A bounded grid track now keeps the page at 390 pixels while table/code blocks scroll inside their containers.
- The admin draft count includes modifications of published/archived records; its link/filter now uses that same definition. Ten counted drafts produce ten listed records in the final fixture.

No automated domain test suite was added or run. The stale-write observation used two tabs with one admin identity; it does not claim a simultaneous multi-admin transaction/load exercise. Row/column insertion and undo were observed, but the full editor/clipboard/assistive-technology matrix and every size boundary remain integrated acceptance work. Draft discard and replacement of an existing draft are implemented with explicit confirmation/version checks but were not exercised as destructive browser scenarios. Trigger installation is recorded; direct SQL attempts to corrupt history were not run.

The existing upstream HTMX eval build warning remains. Evaluation is disabled and CSP is unchanged; `unsafe-eval` was not added. No image renderer, paid editor extension, embedding model or remote answering API was introduced by M3.

## Cleanup and next milestone

Inspection services are stopped after capture, retaining the isolated fictional volumes. Temporary credential pipe metadata is removed and session credentials are cleared. The normal development database is migrated independently and remains empty of accounts/content for the owner's bootstrap and explicit import. [Normal database snapshot](evidence/m3/normal-database.json).

M4 is next: epics, user stories and shared sprints with activation, closure and retained snapshots. M5 delivers files/previews; M6 completes search/chatbot and must satisfy the unresolved M0 retrieval quality gate. Real hosting, HTTPS/proxy/SMTP, backup/restore, concurrency/load and assembled-release acceptance remain M7. Remote CI has not run, and these changes have not been committed or pushed during this milestone.
