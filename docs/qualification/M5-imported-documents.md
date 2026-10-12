# M5 — Imported documents

Date: 2026-10-12

Status: implemented and observed locally on `main`. M6 search/chatbot is next; integrated acceptance, the broader accessibility matrix, concurrency/load and real-host operation remain M7 work. No automated test suite was added or run for this milestone.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md), [ADR-004](../adr/004-m0-preview-and-retrieval-decisions.md). French usage and operator guide: [portal README](../../portal/README.md).

## Delivered

- Document drafts/publications with title, approved category, description, required published applications and optional epic/story/specification links. Reader library search/category/application filters, reciprocal links and existing publication/archive/restoration lifecycle now include documents.
- Private streamed uploads, bounded request handling, immutable source identity/digest/category/filename/format/options and a separate preparation result. A ready result is frozen. New imports freeze format options and source/preview bounds; job identity includes file identity and a fingerprint of digest, adapter version, format and options.
- Original writes precede the serialized metadata transaction. Conflict/authorization/validation failures remove the staged bytes. Replacements attach only to drafts. Ready-only publication and PostgreSQL guards reject missing, cross-document or unready files.
- File foreign keys are copied by begin-edit and historical restoration, and retained by immutable content publications. Restoring an old file changes a draft; readers retain the current publication. Archives remove current file eligibility without deleting retained history.
- A preview-only worker with row locks, leases, fencing tokens, immutable-source digest verification, bounded child processes and private attempt directories. Permanent format failures stop immediately; transient failures have at most three automatic attempts with backoff. Explicit admin retry never publishes. Semantic jobs remain pending for M6.
- Offline adapters: compressed/uncompressed multi-page draw.io; `.xlsx` stored values/formula-cache distinctions/simple formats/hidden sheets; strict UTF-8 CSV with explicit separator override; local multi-block PlantUML/Smetana; sanitized PDF page delivery to local PDF.js; decoded/re-encoded PNG/JPEG; allowlisted SVG rasterization.
- Table consultation renders at most 100 rows per page and keeps all approved sheets selectable. Formula metadata is inert text. Missing cached results are distinguished from genuine cached empty strings. Diagram/image/PDF pages expose selection and zoom controls.
- Diagram viewers receive only authorized derived data from the parent page. Their sandbox excludes same-origin access; viewer CSP permits local scripts/fonts, local PDF decoders and derived image blobs, with no remote diagram service. PDF JavaScript evaluation/actions/XFA are disabled. WebAssembly permission is confined to the isolated frame.
- Every original/asset/frame/status request resolves either the current published file or an explicitly admin-only draft/history revision. Stale current-revision parameters do not expose historical originals. Originals are SHA-256 verified before attachment delivery; raw SVG/PDF/text sources are never embedded as active originals.
- Admin preparation-state filters, actionable errors with mechanical observed-limit details, polling that preserves dirty input, explicit retry and cleanup tooling. Cleanup defaults to a dry run, retains draft/publication references and active jobs, and requires at least a 24-hour grace before removing abandoned objects.
- Reproducible digest-pinned assets, retained notices and Linux ARM64 packaging with Java/Cairo. Draw.io 32.4.1 includes its matching stencil bundle and 9,089 validated names; PlantUML MIT 1.2026.8 and PDF.js 6.4.299 retain the M0 choices. Native setup and CI now acquire the same assets. CI changes were not executed remotely.

## Local environment and actual state

The existing `ubsi-portal-m2-preview` Compose project and its two previously authorized fictional accounts were reused. Equivalent password rotation used terminal stdin without password files/output or role/access expansion. Browser sign-in used the existing credentials; no credential-creation/reset form was submitted. Only generated M0/M5 synthetic sources were imported. User spreadsheet files at repository root were untouched.

The isolated database has **29 migrations**, **31 records**, **36 published revisions**, **11 drafts** and **25 immutable sources**. Twelve document records produced thirteen publications; eleven documents remain published and one is archived. Twenty previews are ready; five deliberately invalid/unsafe/over-limit preparations remain failed and unreferenced after correction. Seven further representative preparations reached ready with frozen bounds, then their temporary drafts were discarded. The restored CSV draft remains separate from its current publication. All 25 original digests and all recorded derived-asset digests match their files. [Runtime snapshot](evidence/m5/runtime.json), [final preparations](evidence/m5/final-preparations.json), [preparation results](evidence/m5/final-preparation-results.json).

The four new PostgreSQL file guards are installed. Imported documents contribute **zero** chatbot passages; the nine existing passages still reference current eligible sources. Five semantic jobs remain pending and ten superseded. The preview worker does not consume them. [Runtime snapshot](evidence/m5/runtime.json).

## Observations

| Area | Observed result | Evidence |
| --- | --- | --- |
| Build/framework | Django check, migration drift/check, TypeScript/Vite, native static collection, Linux ARM64 image construction and root CSV conversion succeed (10/0/0 CSV rows). Native collection includes 215 assets; the image also generates the PlantUML license text | [Build/check log](evidence/m5/checks-build-export.log), [image/framework metadata](evidence/m5/container-checks.log) |
| Private import/publication | UI creates DOC-001 metadata, imports a fictional XLSX and blocks publication while preparation is not ready. After correction/retry, the admin previews both sheets and explicitly publishes it | Browser notes and runtime state |
| Approved formats | Eleven approved extensions plus a paginated CSV were imported using the shared service. All initial valid sources reached ready; further representative draw.io/XLSX/CSV/PlantUML/PDF/PNG/SVG inputs also reached ready | [Initial imports](evidence/m5/service-imports.json), final preparation results |
| draw.io | Native and XML sources prepare. Viewer shows HTML labels, a bundled named stencil, a validated inline stencil and embedded PNG; the compressed second page displays its distinct label. Eleven rendered SVG shapes were observed on the first page | [Admin view](evidence/m5/drawio-desktop.jpg), [compact reader view](evidence/m5/drawio-reader-compact.jpg), browser notes |
| Workbook | Numeric/date/percentage/bold values display; formula B3 shows `3`, genuine empty B4 stays empty, absent/empty-numeric caches B5/B6 show “Résultat non disponible”. Hidden sheet remains selectable with its badge | [Reader workbook](evidence/m5/spreadsheet-reader-desktop.jpg), browser notes |
| CSV | Quoted delimiters and embedded newlines remain intact. A deliberately ambiguous replacement fails automatic detection, then succeeds with explicit semicolon. A 205-row source has three pages; page two starts at row 101 | [Pagination](evidence/m5/csv-pagination.jpg), [replacement operations](evidence/m5/replacement-operations.json), file history |
| PlantUML | Two UML blocks prepare into two PNG pages and can be selected in the viewer; the `.plantuml` alias also prepares. An include source fails with `unsafe` | [UML view](evidence/m5/plantuml-desktop.jpg), runtime/preparation snapshots |
| PDF/images | PDF renders both pages on local PDF.js canvas with zoom. PNG/JPG/JPEG and rasterized SVG display; observed JPG/JPEG are 520×160, SVG 720×220 | [PDF](evidence/m5/pdf-desktop.jpg), browser notes |
| Isolation | In-frame diagnostics report parent access `blocked`; the parent receives authenticated viewer messages with opaque origin `null`, for both draw.io and PDF | [Browser notes](evidence/m5/browser.json) |
| Responsive reader | Workbook and diagram observed at 390px with page width 390, menu navigation and table keyboard scrolling from 0 to 40px. The table has a 314px viewport and 578px content | [Mobile workbook](evidence/m5/spreadsheet-reader-mobile.jpg), [mobile diagram](evidence/m5/drawio-reader-mobile.jpg) |
| Exact originals | Admin PlantUML download and reader XLSX download match the uploaded bytes and SHA-256. Every stored source in the snapshot also matches its recorded digest | [PlantUML download](evidence/m5/download-plantuml.json), [XLSX download](evidence/m5/download-spreadsheet.json), runtime snapshot |
| Failed replacements | Malformed PNG, active SVG and PlantUML include are refused; publication of the failed PNG draft is blocked while its existing live image remains available | [Admin refusal](evidence/m5/replacement-failed-admin.jpg), [live original](evidence/m5/replacement-live-unchanged.jpg), [failure states](evidence/m5/previews-after-replacements.json) |
| Limits | A 20 MiB + 1 replacement is refused by the upload service. A workbook with 51 sheets fails with observed 51 / permitted 50, without replacing its published workbook | [Operations](evidence/m5/replacement-operations.json), [worksheet refusal](evidence/m5/worksheet-limit-refused.jpg) |
| History/restoration | CSV v2 has the corrected original; admin v1 still shows the earlier source. Restoring v1 copies that file into a draft while the reader continues to see v2 | [Admin file history](evidence/m5/file-history-admin.jpg), runtime snapshot |
| Access/archive | Reader UI has no admin links. An old current-download version returns an unavailable page; the admin historical-download URL is denied to the reader. Archiving DOC-010 removes its reader page | [History denied](evidence/m5/history-reader-denied.jpg), browser notes |
| Queue restart | Four replacement jobs queued with the worker stopped are processed after restarting it. Final jobs complete before their temporary drafts are discarded | Failure states and final preparation results |
| Cleanup | Dry run completes with zero currently aged candidates. No retained original/history or mature object was deleted | [Dry run](evidence/m5/cleanup-dry-run.log) |
| Anonymous delivery | Health/live and readiness respond 200. Anonymous private pages/download/frame/history redirect to the clean login URL; asset/status APIs return 401. Public fixed vendor modules have CORS for the opaque viewer | [HTTP observations](evidence/m5/public-http.json) |

The normal local database is migrated separately and remains empty of fictional accounts/content/files. [Normal database snapshot](evidence/m5/normal-database.json).

## Corrections and limits

- Excel parsing uses a file-like object: the private storage key intentionally has no user-supplied extension. Stencil preflight supports the safe inline shapes already qualified in M0, plus validates parent/endpoint references and rejects parent cycles.
- A final Docker extraction-cache error cleared on retry without pruning shared caches. The final image/framework metadata records the successful rebuild.
- Java requires a larger **virtual address-space** allowance than its heap. The isolated child uses 4 GiB virtual address space, a 256 MiB Java heap and bounded class/code memory; Compose still caps worker resident/cgroup memory at 2 GiB. Other parser children use 1,536 MiB virtual address space. These are engineering controls, not measured real-host sizing guarantees.
- Generated previews have a cumulative byte budget. draw.io page inflation permits bounded URI encoding overhead, then enforces the decoded XML bound. CSV detection tries the other candidate separators before treating an over-limit candidate as the final interpretation.
- PDF.js runs its bundled worker handler inside the isolated frame. Its “Setting up fake worker” warning is expected; no remote worker runs. Actual preview latency and uncommon PDF codecs/fonts still need the M7 representative-source matrix.
- Initial viewport requests did not change the inspected tab; another owned tab provided the actual 390px viewport. Only measured 390px pages are labelled mobile evidence. Desktop widths 1280/1072 and compact width 747 were also observed. A broader device, keyboard and screen-reader matrix remains M7 work.
- This milestone did not exercise simultaneous workers/admin uploads, hard crash during rendering, lease expiry/reclamation, actual aged-file deletion, direct SQL attempts to corrupt history, every boundary format/limit, or load/host backup/restore. Code includes the relevant locks, fencing, references and bounds; installed triggers and dry-run results are recorded without claiming those remaining scenarios passed.
- Complex unsupported resources fail visibly rather than being silently truncated. Excel charts/conditional formatting/merged-cell layout and interactive PDF features are outside the approved preview scope. Custom draw.io libraries and external PlantUML dependencies require simplification or another approved exported source.

## Teardown and next milestone

Owned browser tabs and fictional sessions are closed, the temporary viewport override is reset, and owned preview services are stopped without deleting database/private volumes. Runtime data remains outside the public repository. No deployment, commit or push was performed.

**Next: M6 — reader search and grounded FAQ assistant**, retaining the M0 retrieval-quality gate. Neither measured M0 retrieval policy is accepted for shipment as the final chatbot.
