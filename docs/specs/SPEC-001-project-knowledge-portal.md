# SPEC-001: UBSI project knowledge portal

status: ready

Review: approved by the project owner on 2026-10-11; proceed to the implementation plan

Created: 2026-10-11

Updated: 2026-10-11

Decision: [ADR-003](../adr/003-project-knowledge-portal.md)

Language: specifications in English; user interface and project content in French.

## 1. Purpose and specification status

Provide UBSI members with one private website for browsing project knowledge: applications, epics, user stories, sprints, written specifications, data flow diagrams, spreadsheets, database diagrams and FAQ entries. Administrators maintain and publish this knowledge. Readers consult it and ask a chatbot for directions to existing answers.

This specification precedes the implementation plan. No application code should be written until it is ready. Work takes place directly on `main`, as requested by the project owner.

Sections marked **Confirmed** record direct choices by the project owner. Detailed rules previously marked **Proposed** were accepted when the owner approved proceeding to the implementation plan on 2026-10-11, and are now marked **Approved**. Section 14 records the approved baseline and the technical inputs deferred to implementation planning. The hosting environment is supplied externally and its capabilities are not known yet; framework, deployment and retrieval technology will be selected in the implementation plan after functional review.

## 2. Confirmed scope

| ID | Requirement |
| --- | --- |
| C-01 | The website is private. All readers and administrators must sign in. |
| C-02 | There are two roles: reader (`user`) and administrator (`admin`). |
| C-03 | Readers have read access to published project content and the chatbot. They cannot create or modify project content. |
| C-04 | Administrators can create, edit and publish project content, including epics, user stories and documents. |
| C-05 | Content is organized by application. An epic may concern multiple applications. A user story belongs to one epic and identifies its relevant applications. |
| C-06 | Sprints are shared across the project. User stories can be assigned to sprints. |
| C-07 | Specifications are editable text pages linked to applications, epics and user stories. |
| C-08 | Administrators import files; members can preview them inside the site and download the originals. Native editing of these files inside the site is outside the confirmed initial scope. |
| C-09 | Imported content includes draw.io data flow diagrams, Excel/CSV spreadsheets and database UML diagrams in draw.io, PlantUML, PDF and image formats (PNG, JPEG, SVG). Section 6 defines extensions and preview details. |
| C-10 | Content follows a draft and publish workflow. Changes to already published content require explicit publication. |
| C-11 | The chatbot searches published FAQ answers and the published text of epics, user stories and specifications. Parsing imported files for chatbot answers is outside the confirmed initial corpus. |
| C-12 | When an existing answer fits, the chatbot directs the member to that answer or source passage. Otherwise it tells them to speak to the urbanists. |
| C-13 | The fallback is a message only. It does not send the question to urbanists or open a support request. |
| C-14 | Initial authentication uses email and password, with accounts available only by administrator invitation. A later move to GitHub sign-in must be possible without losing account ownership or content history. |
| C-15 | Sprint scope is objective, dates, user stories, responsible members and work states, with history preserved on closure. Estimates, capacity planning, burndown charts and velocity metrics are outside this first version. |
| C-16 | Spreadsheet previews show cells and stored formula results, with simple formatting. They do not require full Excel layout or chart fidelity. |
| C-17 | Administrators can consult history, restore an earlier version into a draft and archive content. Readers consult the current published version only. |
| C-18 | Specifications use a visual editor with headings, lists, tables, links and code blocks. Markdown authoring is not required. |
| C-19 | The initial team has 46 members. No software/service budget is available. Hosting will be provided, with capabilities still to be specified. |

## 3. Roles and access

### 3.1 Access matrix

**Confirmed role separation; approved detailed permissions.**

| Action | Signed out | Reader | Administrator |
| --- | --- | --- | --- |
| Sign in, accept a valid invitation, recover password | Yes | Yes | Yes |
| Browse published content, FAQ and application pages | No | Yes | Yes |
| Preview or download a published file | No | Yes | Yes |
| Use chatbot and follow its source links | No | Yes | Yes |
| See drafts or unpublished changes | No | No | Yes |
| Create or modify content and relationships | No | No | Yes |
| Publish, withdraw or archive content | No | No | Yes |
| Invite users, deactivate accounts, manage roles | No | No | Yes |
| Browse administrative revision history | No | No | Yes |

Authorization applies to server operations, search results, file access and chatbot retrieval. Hiding a button alone does not grant protection. A reader who requests an administrator operation directly receives a permission error and no change is made. Unauthorized responses must not expose draft titles, snippets or attachment names.

### 3.2 Account lifecycle

**Confirmed:** email/password and invitation-only access; future GitHub sign-in.

**Approved rules:**

- An administrator invites a person by email and assigns their role. Public self-registration is unavailable.
- The invitation is single-use and expires after a configured period. The invited person chooses a display name and password; the invited email is fixed during acceptance.
- Reinviting a pending account replaces its previous invitation. Inviting an active email returns a clear existing-account result rather than creating a duplicate.
- Password recovery uses a single-use expiring link. Its public response does not reveal whether an email has an account.
- Administrators can deactivate an account. Its existing authorship remains; future sign-in and existing sessions lose access.
- Removing or demoting the last active administrator is rejected.
- The first administrator is provisioned through a controlled bootstrap operation. No initial password is committed to the repository.
- User identity has a stable internal identifier, independent of email and login provider. Later GitHub linking requires proof of account ownership; matching an email alone must not silently merge identities.
- Invitation lifetime, password requirements, session lifetime and first-admin provisioning are finalized in the implementation plan.

## 4. Content structure and fields

**Confirmed entity types, high-level relationships, visual editor and sprint scope; approved detailed field contract.**

### 4.1 Shared fields

Every content record has a stable identifier, title, publication state, creation and modification timestamps, author attribution and revision information. Its URL remains stable when its title changes. Reference codes, such as `EPIC-001`, `US-001` and `SPEC-001`, are unique and never reused. The implementation plan fixes the concrete reference-code conventions without changing stable identity requirements.

Publication state is separate from work progress: a published user story may be in the backlog, in progress or complete. A completed item remains readable as project history. Under the approved uniform workflow, changes to reader-visible work states, sprint assignments and relationships also require publication; a future quick-update action must publish an explicit revision rather than bypass this rule.

### 4.2 Application

- Required: unique application code, name and description.
- Approved initial application directory: one-time import from `data/applications.csv`, preserving codes, names, types and descriptions. After import, administrators maintain the portal directory; no automatic bidirectional synchronization or overwrite from Git is part of this version. The existing CSV/Release workflow keeps its own ownership until a later explicit decision.
- The detail page lists linked epics, user stories, specifications and documents.
- A record associated with several applications appears under each application using the same record and URL.
- Changes to an application code must not break existing relationships or URLs.

### 4.3 Epic

- Required at publication: title, objective, description, scope and at least one application.
- Optional: exclusions from scope, acceptance conditions, owner and target date.
- Approved progress states: `planned`, `in_progress`, `completed`, `cancelled`.
- The detail page lists its user stories, linked specifications and documents, plus relevant sprints derived from its stories.
- An epic is a grouping of work. It can span several sprints.

### 4.4 User story

- Required at publication: title, exactly one epic, at least one application, user/actor, need, expected benefit and at least one acceptance criterion.
- Approved applications must be a subset of the parent epic's applications. Removing an epic application that would invalidate an existing story is rejected until the links are resolved.
- The interface provides structured fields corresponding to: “En tant que …, je veux …, afin de …”.
- Acceptance criteria are individually readable text items. They may use Given/When/Then wording without requiring that syntax.
- Optional: context, dependencies on other stories, owner, priority and current sprint.
- Approved work states: `backlog`, `ready`, `in_progress`, `in_review`, `done`, `cancelled`.
- Approved priority values: `low`, `normal`, `high`, `critical`.
- Approved dependency rule: a story cannot depend on itself or introduce a cycle. Dependencies are informative links; they do not automatically block work-state transitions or change another story's status.
- The detail page exposes the parent epic, relevant applications, acceptance criteria, sprint, specifications and documents.
- Estimates, capacity planning and agile metrics are outside this first version. Technical subtasks and blocking-dependency automation are optional later extensions.

### 4.5 Sprint

- Required at publication: name, objective, responsible member, start date and end date; end date must be on or after start date. The responsible member can be a reader; this attribution does not grant editing permissions.
- Sprints belong to UBSI as a whole, not to an application.
- Approved states: `planned`, `active`, `closed`.
- The page lists assigned user stories and their work progress, with application and epic filters.
- A user story has at most one current sprint assignment. Closed-sprint membership is stored independently and does not prevent a story from appearing in a later sprint.
- The approved first version allows one active sprint at a time. Planned sprint dates may overlap, but activating a second sprint is rejected until the active one is closed. Dates alone do not activate or close sprints.
- Assigning a story to an active sprint requires a published story and a responsible member on that story. A reader assigned as responsible still has read-only access; administrators update and publish progress.
- Approved state transitions: `planned` to `active`, then `active` to `closed`. Starting or closing is an explicit administrator publication action. Closing is rejected while the sprint or its assigned stories have unpublished changes that would make the snapshot ambiguous; administrators publish or discard those changes first.
- Closing records an immutable snapshot of the sprint objective/dates/owner and each assigned story's identifier, title, epic, applications, owner and work state at closure. Later changes to the story must not rewrite that snapshot.
- The closing screen lists incomplete stories and requires an explicit decision for each: return it to the backlog or carry it into a selected planned sprint. Historical membership and state at closure remain unchanged. Finished/cancelled stories leave the current assignment but remain in the closed snapshot. Carry-over does not automatically change work state.
- Carrying a story into a future sprint must not silently displace another current assignment; conflicts require explicit resolution. The close operation either completes with its snapshot and assignment updates or leaves all of them unchanged. The administrator explicitly publishes the listed assignment updates as part of closure; they create new story revisions without rewriting older revisions.
- Closed sprints remain readable as published project history. They cannot be reopened or have their snapshot edited in this version. Archiving a sprint uses the general archive rules.
- A closed-sprint row links to the story's current published page and labels its stored work state “À la clôture”. If the story is no longer reader-visible, its details/link are replaced by an unavailable marker; the original snapshot remains available to administrators.
- No story points, capacity forecasts, burndown charts or velocity metrics are required.

### 4.6 Written specification

- Required at publication: title, text body and at least one application.
- A specification may reference several epics and user stories. Their detail pages show the reciprocal links.
- Confirmed visual editor features: headings, paragraphs, lists, links, tables and code blocks, with a reader preview. Administrators format text through controls without writing Markdown.
- Approved editor details: ordered/unordered lists, bold/italic text, undo/redo, table row/column editing and plain-text code blocks. Heading sections receive stable identifiers when created; changing a heading title preserves its existing anchor. Deleted sections lead to the current specification with a visible missing-section notice.
- Approved content template: context, objective, scope, functional rules, linked data flows, acceptance criteria and unresolved questions.
- The chatbot can point to a specific published section using a stable section link.
- A specification can link imported documents without copying their contents into the page.

### 4.7 Imported document

- Required at publication: title, category, description, at least one application and a valid uploaded source file.
- Categories: `data_flow`, `spreadsheet`, `database_diagram`.
- Optional links: epics, user stories and written specifications.
- Preserve the original filename, file format, byte size, upload time, uploader and revision identifier.
- Replacing a source creates a new file revision rather than silently overwriting the previous file. Old published originals and previews remain available to administrators through history, but are not accessible to readers.
- A document attached to a draft is accessible only to administrators. File URLs must follow the document's effective publication and access state.
- A published document can be linked by multiple records; there is only one canonical document record.
- Uploaded sources are runtime data. Whether existing repository files are imported or remain linked is a migration decision; uploading binary files to the public Git repository is not the default storage mechanism.

### 4.8 FAQ entry

- Required at publication: question and answer text.
- Optional: alternative formulations, category, application links and supporting content links.
- Administrators author and publish FAQ entries using the same publication workflow.
- Readers can browse the FAQ directly, search it and open an individual answer through a stable URL.
- Alternative formulations help retrieval; they do not become separate duplicate FAQ records.

## 5. Draft, publication and history

**Confirmed:** explicit publication for initial content and subsequent changes; administrator-only revision history, restoration into drafts and archiving. Readers see only the current published version.

**Approved detailed behavior:**

1. Creating content starts an administrator-only draft. Saving it does not publish it.
2. Publishing checks all required fields, permissions, links and files. Errors identify the fields to fix and preserve the draft.
3. A successful publication makes a complete revision available to readers and to the chatbot corpus where applicable.
4. Editing published content creates a working draft. Readers continue seeing the last published revision until its replacement is published.
5. The administrator can preview the working draft, publish it or discard unpublished changes.
6. Publication must not expose a partially saved revision or mixed text and files from different revisions.
7. A reader-visible item cannot link to a draft-only parent or required target. Publishing is rejected until required targets are published. Optional draft links are resolved before publication rather than leaked to readers.
8. Withdrawing content immediately removes it from reader navigation, reader search, source links and chatbot eligibility. Previously issued download links must also respect access withdrawal. A later chatbot answer must never serve stale withdrawn text.
9. Administrators can archive obsolete records, consult previous published versions and restore a version into a draft. The detailed approved rules below preserve required relationships and published history.
10. An edit based on an outdated draft revision must not silently overwrite another administrator's work. Show the conflict and preserve the pending edits for recovery.

Audit timestamps are stored consistently and displayed in the project timezone, Europe/Paris. User-facing author identity must not require exposing email addresses.

### 5.1 Revision history and restoration

**Confirmed capabilities; approved detailed rules:**

- Preserve every published text/metadata revision and every published document-file revision, with author and publication timestamp. File previews belong to their source revision.
- A working draft has one current saved state; retaining every keystroke or every unpublished autosave is not required.
- The administrator history view lists versions and can open their text, fields and authorized file previews/downloads. Comparing text versions is useful but an automatic visual diff is not required in this version.
- Restoring a previous version copies its fields, relationships and original-file references into a new working draft. The published revision remains unchanged. If a draft already exists, ask before replacing it.
- A restored draft undergoes current field, relationship and file validation before publication; old references cannot bypass current visibility rules.
- Readers cannot select historical revisions or download their files through direct URLs. Closed-sprint snapshots are current published historical records, rather than access to previous content revisions.

### 5.2 Archive and withdrawal

- Approved publication states are `draft_only`, `published` and `archived`; a published record may additionally have a working draft.
- Archiving withdraws the current published record from reader pages, search and chatbot eligibility, while preserving its identifier, history and files for administrators.
- Archiving is rejected if it would leave an active published required relationship without a visible target. Reassign or archive dependent records first. No automatic cascade is performed.
- Optional references to an archived record are hidden from reader link lists. Historical sprint rows use the unavailable-marker rule in section 4.5.
- Restoring an archived record produces an administrator-only draft. It does not republish the old record automatically.
- Approved deletion rule: discard a never-published, unreferenced draft; retain previously published records through archiving. Permanent removal of published history is not offered in the initial administrator interface.
- Files shared by retained revisions remain stored. Cleanup may remove only files no longer referenced by any retained draft, published revision or archived record.

## 6. File import, preview and download

**Confirmed:** import, in-site preview and original download; draw.io, PlantUML, PDF and image diagrams; Excel/CSV with cell values, stored formula results and simple formatting.

**Supported families confirmed; approved extension-level contract and preview rules:**

| Category | Source formats | Reader preview | Original download |
| --- | --- | --- | --- |
| Data flow diagram | `.drawio`; draw.io XML after content validation | Read-only diagram, zoom, pan and page selection for multiple-page sources | Exact uploaded source |
| Spreadsheet | `.xlsx`, `.csv` | Sheet selection, column headers and scrollable cells; configured delimiter/encoding handling for CSV | Exact uploaded source |
| Database diagram | `.drawio`, `.puml`, `.plantuml`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.svg` | Rendered diagram/image or PDF, with zoom and page selection as applicable | Exact uploaded source |

Extensions in this table define the approved initial format contract. `.xls`, `.xlsm`, zip archives, remote PlantUML includes and additional formats are outside the approved initial contract. Compressed and uncompressed diagram data inside native `.drawio` XML must both be supported.

### Import workflow

1. An administrator selects a category, supplies metadata and uploads a source file.
2. The site validates actual content against the allowed format and size; changing an extension is insufficient.
3. The source is stored privately. Preview preparation reports `processing`, `ready` or `failed`.
4. A failed preview gives an actionable message. Approved publication rule: block publication of a revision whose preview is not ready. If a replacement fails, readers keep the previous published source and preview; the administrator can retry or supply a corrected file.
5. The administrator reviews the preview and publishes the document. Readers see only the published file revision.

### Preview rules

- Spreadsheet consultation is read-only. Macros, external links and embedded scripts never execute.
- Spreadsheet previews show stored cell values and cached formula results without recalculating Excel formulas. A formula with no saved result displays “Résultat non disponible” and an explanation that the workbook must be recalculated and saved in Excel or another spreadsheet editor before reimport. A genuine empty cached result remains empty rather than appearing as an error.
- Approved simple formatting: readable column/row labels, numeric/date/percentage display, bold text and line breaks. Pixel-perfect dimensions, charts, conditional formatting and merged-cell layout are outside scope. For merged cells, show the stored value in the top-left cell and explain that the preview simplifies the original layout.
- PlantUML includes and external diagram resources must not silently fetch private or remote resources. Uploaded SVG and diagram previews must not execute active content.
- A multi-page diagram or multi-sheet workbook exposes all supported pages/sheets. Approved hidden-sheet handling: include them in the read-only selector with a “Masquée dans le fichier original” badge. Original downloads already contain those sheets; hiding a sheet in Excel is not an access-control boundary.
- Approved CSV handling: UTF-8 with or without BOM, comma/semicolon/tab separators, auto-detection with an administrator override before publication when ambiguous. Invalid encoding or an inconsistent parse gives a correction message; no silent column shifts. CSV files have one logical sheet and no formula evaluation.
- Unsupported preview features must produce a visible limitation message rather than claim full Excel fidelity.
- Original downloads return the uploaded bytes and filename. Derived previews do not replace the source.
- Upload and preview limits are shown before file selection. A source beyond a supported limit is rejected with the observed limit, a correction hint and no partially published document.

### 6.1 Approved initial limits

The owner expects modest files but has not provided measurements. These are approved configurable defaults, not observed file sizes; the implementation plan must check representative files and available hosting resources.

| Resource | Approved default |
| --- | --- |
| Source file size | 20 MiB per file |
| Spreadsheet worksheets | 50 per workbook |
| Populated spreadsheet cells | 200,000 across the workbook |
| Spreadsheet extent | 20,000 rows and 200 populated columns per worksheet, ignoring unused formatting beyond the data extent |
| Expanded workbook package | 200 MiB total uncompressed data; reject abnormal archive expansion before full processing |
| Diagram/PDF pages | 50 per source |

Large supported workbooks use paginated/virtualized consultation rather than rendering every cell at once. Over-limit sources must never be presented as successfully imported after silently truncating their content. Total file-history storage and backup capacity are hosting decisions, not a promise of unlimited physical storage.

## 7. Reader experience

**Approved screen inventory derived from confirmed scope:**

- Sign-in, invitation acceptance and password recovery pages.
- Home page with application access, the active sprint when present and entry points to search, FAQ and chatbot.
- Application directory and detail pages.
- Epic and user-story lists and detail pages.
- Sprint list and detail pages, including past sprints.
- Specification list and section-linked detail pages.
- Document library with category/application filters and a preview/download detail page.
- FAQ list and individual answers.
- Chatbot panel accessible from reader pages.

Lists support text search and applicable filters: application, epic, sprint, document category and work progress. Lists and search always use the last published revision available to the reader. Empty states distinguish “no content yet” from “no result for these filters”. A missing or inaccessible item produces a clear unavailable message without disclosing its private details.

The language is French. Reader and admin experiences can share one authenticated application; a separate deployment is not implied by the requirement for two views.

## 8. Administrator experience

**Approved screen inventory:**

- Administration dashboard with drafts, published items with unpublished changes and preview-processing failures.
- Content lists with create/edit actions, publication state filters and published-page links.
- Forms for applications, epics, user stories, sprints, specifications, documents and FAQ entries.
- Reader preview of a draft with a clear unpublished indicator.
- Publication action that lists blocking validation errors.
- User invitations, account deactivation and role management.
- Administrator-only revision history, restoration into drafts and archive management.

Readers never see administrative creation or editing controls. Administrator pages must still enforce authorization for every read and write operation. Switching views does not change the account's permissions.

## 9. FAQ and chatbot

### 9.1 Authorized corpus

**Confirmed:** published FAQ entries and the published text of epics, user stories and specifications.

- FAQ questions, aliases and answer bodies are eligible.
- Epic and user-story titles, descriptions and associated textual sections are eligible; specification titles and body sections are eligible.
- Drafts, unpublished changes, imported-file contents, credentials and account information are excluded.
- Archived records stay available to administrators through history/archive views. Approved retrieval rule: exclude them from chatbot answers and reader navigation, even when the requester is an administrator using the reader chatbot.
- Each searchable passage retains its canonical record, published revision and section anchor where applicable.

### 9.2 Answer contract

**Confirmed:** guide users to an existing answer; otherwise refer them to urbanists.

**Approved concrete behavior:**

1. A reader submits a natural-language question in French.
2. An empty/whitespace-only question is rejected locally with an input hint and creates no request.
3. The site searches only eligible sources. Similar wording alone is insufficient: a returned passage must answer the user's actual question.
4. When one source is adequate, display its title, a short verbatim excerpt and an action such as “Voir la réponse” or “Consulter la spécification”, linking to the exact published answer/section. Do not navigate away automatically.
5. When several sources jointly answer the question, show up to three source cards with their excerpts. Do not invent a combined explanation unsupported by those passages.
6. Approved ambiguity policy: when available sources conflict or the question is insufficiently precise to select an adequate answer, use the urbanists fallback. The chatbot does not invent a resolution or assume a newer timestamp means a business rule is authoritative.
7. When no adequate source exists, display: “Aucune réponse adaptée n’a été trouvée. Allez en parler aux urbanistes.” This approved exact wording can be adjusted without changing the fallback rule.
8. The fallback contains no contact channel, outbound message action or support-ticket creation.
9. On a technical failure, display a retry message distinct from “no answer found”. Do not claim the knowledge base contains no answer when retrieval failed.
10. Recheck source visibility and current published revision before sending an answer and before opening it. A stale retrieval index must not expose withdrawn content, unpublished revisions or obsolete answers from a replaced revision. While indexing catches up, use a verified current source or report temporary unavailability rather than falsely claim no answer exists.

The implementation may use keyword retrieval, semantic retrieval or a model, but none is selected yet. The zero-budget constraint excludes a mandatory paid API or license. If a model is used, retrieved content is data, not instructions. Generated statements must not add facts beyond authorized sources. Any third-party processing of private content requires an explicit hosting/data-handling decision; the functional design must support processing on the provided infrastructure.

### 9.3 Conversation and storage

Persistent chat history, question analytics and unanswered-question collection are not confirmed features. Approved first version: session-only messages, no automatic transfer of questions to administrators, no durable transcript collection, and each submitted question interpreted independently. Contextual follow-up questions remain an explicitly optional extension.

### 9.4 Retrieval acceptance examples

Before choosing the retrieval method or threshold, build an agreed example set containing:

- A question identical to a published FAQ question: return that FAQ answer.
- A paraphrase of that question: return the same adequate answer.
- A question answered only in a published specification section: link that section.
- A question with a keyword present in a document but no actual answer there: use fallback.
- A question answered only in a draft or unpublished revision: use fallback unless another published source answers it.
- A question requiring information inside an Excel or diagram file only: use fallback in this version.
- Two conflicting published passages: avoid a definitive unsupported answer.
- A withdrawn answer still present in a stale index: never return that passage.
- An outdated answer from a replaced published revision: return verified current text or temporary unavailability, never the obsolete answer.
- A retrieval-service failure: show the technical error and retry option.

The project owner/urbanists supply representative UBSI questions and acceptable destinations. An arbitrary similarity score is not a business acceptance criterion.

## 10. Data and revision model

**Approved conceptual model, independent of technical database choice:**

| Entity | Relationships |
| --- | --- |
| User | One role; invitation state; account state; stable identity; later one or more verified login identities |
| Application | Linked to many epics, stories, specs and documents |
| Epic | One or more applications; many user stories; linked specs and documents |
| UserStory | Exactly one epic; one or more applications; zero or one current sprint; linked specs and documents |
| Sprint | Many current stories; immutable membership and field snapshot at closure |
| Specification | One or more applications; optional epic/story links; revisioned text sections |
| Document | Category; application/content links; source-file revisions and derived previews |
| FAQEntry | Question, aliases, answer; optional application/content links |
| ContentRevision | Record, author, timestamps, publication state and snapshot of fields and relationships |
| FileRevision | Private original and preview assets; format, size and processing state |

Content relations refer to stable internal identifiers. Publication provides a coherent text/relationship/file snapshot. Restoring an old revision creates a new draft rather than rewriting published history. Approved additional entity: `SprintClosureSnapshot`, preserving sprint fields and story membership/state independently from their current revisions.

## 11. Nonfunctional requirements

**Required consequences of confirmed private access:**

- Enforce sign-in and role checks on all private pages, APIs, original files and preview assets.
- Store account information and uploaded private material outside the public source repository. Use encrypted transport in deployment and a suitable password-hashing mechanism.
- Keep user content safe to render; validate uploads and sanitize authored text and diagram previews.
- Support recovery of published content and uploaded originals. Backup frequency and recovery objectives require an operating decision.

**Approved usability and operation requirements:**

- Core reader flows and forms work with keyboard navigation, visible focus, meaningful labels and readable error messages.
- Reader pages work on desktop and mobile. Large diagrams/tables have appropriate pan, zoom and scroll controls.
- Upload, publication, preview and chatbot operations expose loading, success and failure states. A retry must not create duplicate content.
- Failed saves preserve local edits where possible. Concurrent edits produce an explicit conflict.
- Confirmed scale: 46 project members. This is a sizing baseline, not a hard registration limit. Hosting is provided and there is no budget for mandatory paid software or consumption-based services.

### 11.1 Approved service targets

- Use 46 signed-in members, including five concurrent chatbot requests, as the initial qualification scenario. Agree a representative content/file dataset during the implementation plan rather than inventing actual project volumes.
- Approved targets on a warmed deployment with that dataset: ordinary page/search requests under 2 seconds at the 95th percentile; chatbot results under 5 seconds at the 95th percentile. File transfers and asynchronous preview generation are measured separately. Targets must be validated against the provided host before being promised operationally.
- Approved backup policy: a consistent daily backup of content, accounts, published file revisions and the metadata needed to restore them; retain seven daily and four weekly restore points. Target maximum data loss is 24 hours. Backup destination, restoration procedure and feasible restoration time are implementation-plan decisions based on hosting.
- Deployment must support private persistent storage and a working invitation/password-recovery delivery mechanism. Availability of application runtimes, containers, database, email transport, HTTPS/domain configuration and backups is still unknown.
- Do not assume a GPU, a paid model API, a cloud subscription or unlimited storage. The implementation plan must adapt to the supplied host and document operational prerequisites before deployment.

## 12. Acceptance scenarios

| ID | Scenario and expected result |
| --- | --- |
| AC-01 | A signed-out visitor requests a project page, original file or preview: sign-in is required and no private content is returned. |
| AC-02 | A reader submits a create/edit/publish request directly: it is rejected and stored data is unchanged. |
| AC-03 | An administrator creates an epic linked to two applications and publishes it: the same epic is readable from both application pages. |
| AC-04 | An administrator creates a story with a parent epic, applications and acceptance criteria: publication validates required relationships and the story links back to its epic. |
| AC-05 | An administrator saves changes to a published specification: readers and the chatbot continue using its previous published text until explicit publication. |
| AC-06 | Publication fails because a required field or published parent is missing: the draft survives and the UI identifies the blocking condition. |
| AC-07 | A supported multi-page draw.io source is published: readers can inspect its pages and download the original file bytes. |
| AC-08 | A supported Excel workbook is published: readers can switch worksheets and download the original; they cannot edit it. Formula/hidden-sheet behavior follows the agreed format contract. |
| AC-09 | Each supported database-diagram format has a representative file that can be imported, previewed and downloaded. An unsupported or invalid file gives a clear error. |
| AC-10 | A reader asks a question answered in published FAQ/spec text: the chatbot provides the correct source and opens the relevant answer/section. |
| AC-11 | A reader asks an unanswered question or one answered only in a draft/file: the chatbot uses the urbanists fallback. |
| AC-12 | A source is withdrawn: it stops appearing in reader search, chatbot answers and authorized downloads. |
| AC-13 | An invited member accepts a valid invitation: their account is created once with the assigned role. Expired or reused invitations cannot create another account. |
| AC-14 | An administrator deactivates a member: existing and subsequent sessions lose private access while past authorship remains. |
| AC-15 | A sprint is closed with unfinished work: the agreed closing procedure preserves historical membership and does not silently change the past sprint. |
| AC-16 | Two administrators edit the same revision: an outdated save produces a recoverable conflict rather than losing the more recent changes. |
| AC-17 | An administrator restores an older text/file revision: a new draft is created; readers keep the current version until explicit publication. A reader's direct request for the older revision is denied. |
| AC-18 | After sprint closure, a carried-over story is edited or completed in a later sprint: the closed sprint still shows its original membership and state at closure. |
| AC-19 | A workbook has a formula with a saved value, a genuinely empty saved value and a formula without a saved value: the preview distinguishes all three and performs no formula recalculation. |
| AC-20 | An administrator authors a specification using visual headings, tables, lists, links and a code block: reader rendering preserves those structures and existing section links survive a heading rename. |
| AC-21 | An uploaded source exceeds a size/page/cell limit or its preview fails: publication is blocked with an actionable error; an earlier published document revision remains readable. |
| AC-22 | An administrator archives a required parent still referenced by a published child: the operation is rejected without a cascade or broken relationship. |

These scenarios define the approved implementation acceptance contract; no application tests are run during specification writing.

## 13. Existing repository and implementation boundaries

- Existing reference data is in `data/`; downloads are produced through GitHub Releases. This specification does not require deleting that mechanism.
- Application codes currently exist in `data/applications.csv`. The approved first-version migration is a one-time directory import followed by portal administration, with no automatic synchronization. This approved ownership rule does not alter the existing Release workflow.
- The prior no-website policy is superseded by ADR-003. Source code/specifications may remain in the public repository, while private runtime data does not belong there.
- Existing uploaded repository documents are not automatically copied into the private portal. An administrator selects and imports them through the same validated workflow; no background document migration or synchronization is implied.
- Technical choices are recorded in the linked implementation plan rather than defined as functional requirements by this specification.
- A later implementation plan will map the approved requirements to architecture, migrations, delivery steps, checks and deployment. It must account for the future GitHub identity migration.

## 14. Decision and review register

### 14.1 Decisions settled with the project owner

| Topic | Confirmed decision |
| --- | --- |
| Access | Private site; email/password accounts invited by admins; future GitHub sign-in |
| Organization | Applications, cross-application epics, stories with one parent epic, shared project sprints |
| Publication | Drafts and explicit publication for initial content and later changes |
| Files | Upload, in-site preview and original download; draw.io, PlantUML, PDF/images and Excel/CSV families |
| Spreadsheet preview | Cells, saved formula results and simple formatting |
| Sprint scope | Objectives, dates, stories, responsible members, work states and preserved closure history |
| Revision history | Admin-only consultation and restoration into drafts; archiving; readers see the current published version |
| Specification authoring | Visual editor with headings, lists, tables, links and code blocks |
| Chatbot | Published FAQ/epic/story/spec text; source redirection; unanswered-question message to speak with urbanists |
| Scale and cost | 46 members; no budget; hosting provided; files expected to be modest without measured sizes |
| Hosting capabilities | Explicitly deferred by the owner: to be specified for the implementation plan |

### 14.2 Detailed defaults approved on 2026-10-11

The owner approved proceeding to implementation planning on 2026-10-11. The following defaults are the approved baseline; later functional changes must update this specification explicitly.

| ID | Approved default | Section |
| --- | --- | --- |
| R-01 | Required fields, work states, priorities, application-link constraints and explicit publication of progress changes | 4–5 |
| R-02 | One active sprint; explicit close with backlog/carry-over decisions; immutable closure snapshot | 4.5 |
| R-03 | Format extensions, 20 MiB upload default, preview complexity limits and formula/hidden-sheet behavior | 6 |
| R-04 | Preserve published revisions; restore into a draft; archive with relationship validation; no permanent deletion of published history in the initial interface | 5 |
| R-05 | Chatbot source cards with exact excerpts, at most three sources, fallback on ambiguity/conflict and independent questions without durable transcripts | 9 |
| R-06 | One-time application-directory import followed by portal ownership; no automatic CSV synchronization | 4.2, 13 |
| R-07 | Qualification targets and daily backup defaults, subject to feasibility on the supplied infrastructure | 11.1 |

### 14.3 Implementation-plan and acceptance inputs

- Hosting capabilities: application runtime, container support, database, private persistent storage, email delivery, HTTPS/domain and backup destination. Unknown at the owner's request; the plan must record prerequisites and deployment constraints rather than assume availability.
- Representative files: one native draw.io file, a workbook with multiple sheets/formulas and examples of each diagram format to qualify. No private files should be committed to the public repository for this purpose.
- Representative UBSI questions: urbanists provide answerable questions, paraphrases, unanswerable questions and expected source destinations before chatbot acceptance. Administrators are responsible for maintaining published content and FAQ; a specific named editorial owner is an operational assignment, not another application role.

## 15. Definition of ready

This specification is `ready` following owner approval on 2026-10-11. The next artifact is [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md), followed by application implementation. Hosting capabilities are explicitly deferred to technical discovery; local development can proceed, while deployment requires a compatible environment and a working account invitation/recovery flow. Technical qualifications and representative-file/question acceptance remain implementation work, not unresolved functional approval.
