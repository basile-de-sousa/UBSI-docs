# M0 — Technical qualification of the private knowledge portal

Date: 2026-10-11

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md) and [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md)

Status: **qualification work completed; M1 foundation may proceed. Retrieval policies are not accepted for production.**

## 1. Outcome

The approved document families can be previewed locally with the proposed technology. The native draw.io viewer needs its matching stencil bundle, in addition to `viewer-static.min.js`. PlantUML database diagrams rendered with the built-in Smetana engine, so Graphviz is not required for the initial reference deployment. Preserve a visible failure for unsupported layouts; this is not a promise that every PlantUML feature is supported.

Local CPU retrieval is technically feasible and inexpensive per measured question. However, neither tested abstention policy meets the complete quality target. Keep the original functional requirement: return an adequate existing source or refer the member to urbanists. **Do not ship either probe as the final chatbot.** M6 must improve the policy and pass a new independent evaluation plus the existing regressions before being accepted.

This milestone produces evidence and implementation decisions. The private application, accounts, publication transactions, durable jobs and deployment are subsequent milestones.

## 2. Reproducibility and selected versions

The runnable probes are in [`qualification/`](../../qualification/README.md). Generated fixtures, environment and downloaded artifacts are in ignored `.qualification/`. Only synthetic fixture definitions, measurements and a screenshot are retained in source control. Existing personal spreadsheet/inspection files were not used.

| Component | Measured version / revision | Disposition |
| --- | --- | --- |
| Python | 3.12.14, macOS arm64 | Local probe runtime; Linux packaging still required |
| Django / psycopg / Argon2 | 5.2.17 / 3.3.6 / 25.1.0 | Installed compatibility baseline; no application or database migration claimed |
| draw.io viewer and stencil bundle | 32.4.1 | Pin both; serve locally; retain upstream notices |
| PlantUML | MIT distribution 1.2026.8 | Local PNG output, SANDBOX, Smetana |
| Java | OpenJDK 25.0.2 | Actual local runtime; qualify the host/container JRE in M1/M5 |
| openpyxl | 3.1.5 | Values and styles plus bounded worksheet XML inspection |
| pypdf / PDF.js | 6.20.0 / 6.4.299 | Server structure checks and local browser canvas renderer |
| Pillow / CairoSVG / Cairo | 12.3.0 / 2.9.1 / 1.18.4 | Raster validation and derived SVG-to-PNG preview |
| Sentence Transformers / PyTorch / NumPy | 6.1.0 / 2.14.1 / 2.5.4 | Offline CPU experiments |
| E5 | `intfloat/multilingual-e5-small` at `614241f622f53c4eeff9890bdc4f31cfecc418b3` | 384 dimensions, 512-token maximum |
| Experimental reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` at `1427fd652930e4ba29e8149678df786c240d8825` | Candidate only; not production-approved |

Exact Python versions are recorded in [`requirements.lock`](../../qualification/requirements.lock); direct dependencies are in [`requirements.in`](../../qualification/requirements.in). This is a snapshot of the measured macOS environment, not a completed Linux deployment lock. Public asset URLs and SHA-256 digests, model commits and license notes are in [`assets.lock.json`](../../qualification/assets.lock.json). HTMX 2.0.11, Tiptap 3.31.4 and Vite 8.3.4 are recorded candidates; their integration and complete dependency locks belong to M1/M3. PostgreSQL 17 remains the database choice; no PostgreSQL runtime was exercised in M0.

draw.io code is Apache-2.0; its icon/stencil terms are separate and must be retained. The downloaded stencil notice restricts incorporation in Atlassian products/ecosystem. This project is a separate internal portal. The MIT PlantUML distribution was selected; E5 is MIT and the reranker is Apache-2.0. Preserve exact upstream notices during packaging rather than relabelling all bundled assets under one license. [draw.io source and licenses](https://github.com/jgraph/drawio/tree/v32.4.1), [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small), [reranker model card](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1).

## 3. File probes

**40/40 format checks and 16/16 boundary checks passed.** Machine-readable evidence: [formats](evidence/files.json), [limits](evidence/limits.json). These counts describe the probes, not completion of the portal's acceptance matrix.

| Family | Observed evidence | Production follow-up |
| --- | --- | --- |
| draw.io / XML | Uncompressed and raw-deflate/base64 compressed pages decoded; standalone `mxGraphModel`; two-page browser navigation/zoom; HTML bold label; embedded custom stencil/image; named `mxgraph.flowchart.database` stencil | Complete bounded schema/resource validation, diagram limits and ready-state render validation |
| XLSX | Two sheets including hidden sheet; dates, percent, bold, numeric values; cached numeric formula, genuine empty string, absent `<v>` and empty numeric `<v/>` distinguished | Paginate/virtualize data; shared-string/style/ZIP bounds; merged-layout notice and adversarial real-world cases |
| CSV | UTF-8 BOM, comma/semicolon/tab, quoted separator/newline; explicit override for ambiguous input; invalid encoding and inconsistent rows rejected; table displayed in browser | Admin delimiter selection and errors before publication |
| PlantUML | `.puml` and `.plantuml`; class/entity relationship diagrams; two blocks → two PNG pages; invalid syntax rejected; local/remote includes blocked; subprocess timeout terminates renderer | Integrate private jobs/storage, finite resource limits and layout-error messages |
| PDF | Two pages, navigation/zoom; 50-page boundary; encrypted source detected/rejected; synthetic JavaScript and URI annotation included for browser isolation check | Protected frame/delivery; complexity limits and production browser checks |
| PNG / JPEG / JPG | Decoded fixture, extension alias and browser display; malformed/truncated input and oversized dimensions refused | Full worker adapter, re-encoding and image memory cap |
| SVG | Allowlisted simple geometry/text rasterized locally; script, external image and entity examples refused | Complete allowlist and process isolation; original is authenticated attachment download only |
| Original bytes | SHA-256 preserved in a copied download artifact for all eleven approved extensions/aliases exercised | Verify the actual authenticated HTTP download and history endpoints in M5 |

An empty `<v/>` on a numeric formula cell must not be mistaken for an intentionally empty string result. The probe requires the string cache type for the genuine empty case; `openpyxl(data_only=True)` alone cannot distinguish these cases. No formulas were recalculated. [openpyxl reader API](https://openpyxl.readthedocs.io/en/stable/api/openpyxl.reader.excel.html).

The final warmed streaming scan accepted 200,000 populated cells in approximately **0.70 s**. The limit suite, including fixture generation, took **2.00 s**, with approximately **95 MiB peak RSS** in its Python process. The generated valid workbook was 424,211 bytes. Earlier scans took about 2.35 s; filesystem cache and process environment affect these timings. These measurements cover a compact numeric fixture; they are not worst-case timing for text-heavy/style-heavy/200 MiB packages. The browser demo displays only the small fixture.

Approved size/page/sheet/cell/extent defaults remain unchanged. The ZIP expansion preflight was exercised using synthetic central-directory metadata, without allocating a 200 MiB package. Add actual hostile archives and bounded streaming parser cases in M5. Additional technical defaults for M5 are **16,000,000 image pixels**, **8,000 pixels per side**, **20 s PlantUML subprocess timeout**, **256 MiB Java heap**, **8 MiB expanded draw.io XML per page**, and the existing **60 s total job bound**. Treat these as configurable engineering defaults, qualify them against representative diagrams and the real host, and surface explicit failures rather than truncation.

### Browser isolation evidence

The local in-app browser rendered the fixtures using locally served assets. The draw.io frame uses `sandbox="allow-scripts"` without same-origin access, forms, popups or navigation permissions. Its measured state reports editing disabled, parent DOM unreadable, named stencil present, one SVG canvas and eleven rendered shape elements per page. The source preview uses a restrictive CSP without `unsafe-eval`; inline styles are allowed for the vendor's layout. No external resources, CSP violations or preview errors were observed on the tested files. See the [recorded browser diagnostics](evidence/browser.json) and [full preview screenshot](evidence/preview.jpg).

The additional official `stencils.min.js` bundle resolves named shapes locally. Do not rely on vendor defaults that point at `viewer.diagrams.net`; override paths, disable dynamic code evaluation and retain the CSP. This test covers the sampled stencil, not every named library or custom shape. [draw.io viewer source](https://github.com/jgraph/drawio/blob/v32.4.1/src/main/webapp/js/viewer-static.min.js).

PDF.js is used only to paint pages onto canvas, with `isEvalSupported: false` and XFA disabled. No annotation/action layer is installed. The synthetic source contains a JavaScript open action and external URI annotation; no script dialog or external request was observed during preview. The M0 canvas is in the harness page; the authenticated, restricted production frame remains an M5 integration requirement. [PDF.js API](https://mozilla.github.io/pdf.js/api/).

PlantUML was invoked with `PLANTUML_SECURITY_PROFILE=SANDBOX` as both environment variable and explicit JVM property, headless Java and `-Playout=smetana`. Includes produced explicit nonzero failures. For the remote case, a temporary loopback HTTP server supplied a valid synthetic include: a trusted `UNSECURE` control fetched and rendered it; SANDBOX refused it with **zero HTTP requests**. The control never used project/user data and is not a production profile. SANDBOX blocks external resource access and Smetana is the documented Java layout alternative to Graphviz. [PlantUML security profiles](https://plantuml.com/security), [layout engines](https://plantuml.com/layout-engines).

## 4. Retrieval experiments and rejected policies

The versioned corpus has 24 synthetic source revisions, of which 20 are eligible. It includes FAQ, spec, epic and story text; contradictory published rules; and deliberately excluded draft, archived, document-only and obsolete revisions. Queries cover paraphrases, absent information, misleading keywords and conflicts. There are no actual business facts or member questions.

V1 was calibrated on 30 questions and evaluated on 30 different questions. After observing V1 errors, a reranker experiment was specified and **30 new V2 questions were written before scoring**. V1 held-out questions became regression cases. Both policies chose thresholds using only the original calibration questions and saved the policy before evaluating. Expectations were authored with the fixture, not reviewed by urbanists; real review remains required in M6.

| Evaluation | Correct destination among 18 answerable | Wrong destination | Abstained answerable | Returned a source among 12 unanswerable/conflicting |
| --- | --- | --- | --- | --- |
| E5 V1 calibration | 17 | 0 | 1 | 0 |
| E5 V1 held-out | **6 (33.3%)** | 1 | 11 | 0 |
| E5 + reranker calibration | 17 | 0 | 1 | 0 |
| E5 + reranker new V2 held-out | **16 (88.9%)** | 0 | 2 | 0 |
| E5 + reranker V1 regression | **10 (55.6%)** | 2 | 6 | **1** |

Raw results, including every error and threshold: [V1](evidence/retrieval-v1.json), [V2 and regression](evidence/retrieval-v2.json). The 90% destination target and zero inappropriate-answer condition are **not jointly met**. A high score or a top-two margin is insufficient to establish that the source actually answers the question. In particular, the reranker incorrectly answers an unanswerable lost-baggage query with the generic sprint carry-over page in the regression set.

The eligibility predicate excluded the four ineligible source revisions before ranking. A simulated post-ranking revision/archive change was refused by the final predicate. This proves the probe's predicate behavior only; authenticated, transactional database filtering and concurrent publication behavior remain M3/M6 tests. Lexical PostgreSQL retrieval, aliases, editor chunking and a production response service are not implemented here.

### Measured resources

CPU only, two PyTorch inference threads, sequential questions on macOS arm64:

| Measure | E5 only | E5 + top-8 reranker |
| --- | --- | --- |
| Load including Python imports | 13.14 s | 15.78 s |
| Warm query p50 / p95 | 38.4 / 46.2 ms | 224.0 / 264.9 ms |
| Observed process peak RSS | 746 MiB | 734 MiB |
| Local model directory size | 487 MiB | 957 MiB total |

Different processes/OS paging affect RSS; the lower observed combined-process peak does not imply a lower required memory budget. E5 passage indexing for 20 sources took 0.75 s. Ranking a synthetic repeated matrix of 10,000 vectors had p95 1.87 ms and used 14.65 MiB for float32 vectors. This measures ranking cost, not the relevance or indexing cost of 10,000 distinct real passages.

Models were acquired at pinned commits, then run with offline loading and `device="cpu"`. E5 inputs use `query: `/`passage: ` prefixes and normalized vectors. The reranker processes query/passage pairs locally, consistent with the documented retrieve-and-rerank pattern. Its scores are not probabilities. [E5 usage contract](https://huggingface.co/intfloat/multilingual-e5-small), [Sentence Transformers cross-encoders](https://sbert.net/examples/cross_encoder/applications/README.html).

**M6 gate:** improve retrieval/adequacy/ambiguity handling, keep known failures as regressions, freeze the revised policy, and evaluate at least 30 new independent questions with urbanist-reviewed destinations. Meet the existing 90% / zero inappropriate-source targets, including conflicts, before claiming completion. If that requires a different model or approach, record a new technical decision and remeasure the CPU/memory envelope. No model is authorized to generate business answers or access unpublished/file-only content.

## 5. Hosting, scope and next milestone

The provider's capabilities remain unknown, as already agreed. The measurements do not establish the proposed 2-vCPU/4-GiB deployment minimum: web, worker, PostgreSQL and Java peaks were not loaded together, and no concurrent 46-member scenario or Linux deployment was run. Docker is installed locally but its daemon was not running; M0 did not start it or modify system services. Java/Cairo were already available; only an ignored local Python environment and public artifacts were installed/acquired.

The existing `scripts/csv_to_xlsx.py` conversion completed successfully: applications 10 rows, donnees 0 rows and flux 0 rows. Existing reference CSVs and Release workflows are unchanged.

Proceed to **M1: application foundation**: separate `portal/`, Linux-qualified dependency locks, PostgreSQL/Compose reference setup, configuration checks, migrations, asset build and French shell. Import adapters remain M5 work; final retrieval remains M6 work. Decisions from this report are recorded in [ADR-004](../adr/004-m0-preview-and-retrieval-decisions.md).
