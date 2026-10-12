# M4 — Backlog and sprints

Date: 2026-10-12

Status: implemented and observed locally on `main`. This checkpoint extends the M3 publication lifecycle to epics, user stories and shared sprints. Integrated acceptance, simultaneous concurrency/load and production operation remain M7 work.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md). French usage guide: [portal README](../../portal/README.md).

## Delivered

- Epic drafts/publications with objective, description, scope, optional exclusions/acceptance conditions/owner/target date, multiple applications and the four approved progress values.
- Structured story actor/need/benefit, individually readable acceptance criteria, optional context/owner, four priorities, six work states and typed relationships to one epic, applications, dependencies and at most one current sprint.
- Publication validates required published targets, the story application's subset of its parent epic, reverse consistency when an epic removes an application, self-reference and dependency cycles. Dependencies remain informational; they do not automate work-state transitions.
- Responsible members are user foreign keys, separate from JSON payloads. Attribution does not change roles. New assignments require active members; existing historical attribution may be retained. Active-sprint story assignments and sprint activation require active responsible members.
- Shared sprint records with objective, responsible member and ordered start/end dates. Planned dates may overlap and do not drive automatic transitions. Explicit activation publishes the active state and serializes against the singleton active-sprint pointer.
- Explicit closure validates the entire current membership and draft versions, requires a backlog/carry-over decision for every unfinished story and clears finished/cancelled assignments. Carry-over preserves work state; backlog return sets `backlog`.
- One transaction publishes all affected story revisions, the closed sprint revision and an immutable closure snapshot. A signed 30-minute balance contains story/target versions; stale balances fail without partial updates. Repeating the completed closure returns its existing outcome.
- Snapshot header and rows preserve pre-closure sprint/story revisions, title, epic, applications, owner and work state. Application rows use foreign keys and frozen labels. PostgreSQL triggers and model guards protect snapshot history. The active pointer is cleared inside the closure transaction before publishing the closed state.
- Closed sprint state/metadata cannot be edited or restored to a planned/active version. An identical closed version may be restored for republication after archive; the original snapshot stays intact. The active sprint must be closed before archiving.
- Reader/admin epics, stories and sprint pages, application/epic/progress/priority filters and pagination. Application pages link shared epics/stories; epic pages derive related current and historical sprints. The private home page highlights the published active sprint.
- Current sprint pages list published current assignments. Closed pages show the snapshot with “À la clôture” labels and links to current story pages. Withdrawn stories become unavailable markers; administrator history retains the full snapshot.
- The shared publication primitive retains M3 immutable revisions, authorization, conflict versions, lexical replacement and durable semantic jobs. No worker, file adapter or chatbot was added. No dependency version changed.

## Local observations

The existing `ubsi-portal-m2-preview` Compose project and its two authorized fictional accounts were reused. Only synthetic content and the existing public application directory were used. Existing credentials were equivalently rotated through terminal stdin, with no role/access expansion and no password files/output. Browser sign-in used these existing credentials; no new password was entered through a browser credential-creation/reset form.

The isolated database has **25 migrations**, **19 records**, **23 published revisions**, one active sprint and one closure with three rows. The replayed closure did not create a second snapshot/revision set. The active sprint is `SPRINT-002`; `SPRINT-001` retains source revision 2 and closed revision 3. Nine search passages belong to current visible sources; zero belong to old or withdrawn sources. Five semantic jobs remain pending and ten superseded, with no worker. [Runtime snapshot](evidence/m4/runtime.json).

| Area | Observed result | Evidence |
| --- | --- | --- |
| Framework and build | Django check reports no issues, no migration drift/pending migrations. Native frontend type/build/static collection, Linux ARM64 image build and root CSV conversion succeed (10/0/0 CSV rows) | [Checks/build/export](evidence/m4/checks-build-export.log), [container](evidence/m4/container-checks.log) |
| Service access | Liveness/readiness return 200. Anonymous epics/stories/sprints/admin requests redirect to the clean login URL with private/no-store and restrictive CSP headers | [HTTP observations](evidence/m4/public-http.json) |
| Cross-application content | One epic spans BIL2 and PLA, with a published specification link. Three structured stories publish with criteria, owners and sprint relationships. Epic reader detail derives both sprints and excludes the withdrawn story | Browser observation notes |
| Parent applications | Removing PLA from the epic is refused while US-002 requires it. Correcting the draft and publishing preserves both applications | [Refusal](evidence/m4/epic-application-refused.jpg) |
| Dependencies | US-002 depends on US-001. Trying to publish US-001 → US-002 is refused as a cycle; clearing that draft link and publishing succeeds | [Cycle refusal](evidence/m4/dependency-cycle-refused.jpg) |
| Activation | A planned sprint with US-001 lacking a published owner is refused. Publishing the owner enables activation. Trying to activate Sprint 2 while Sprint 1 is active is refused | [Owner refusal](evidence/m4/activation-owner-refused.jpg), [second active refusal](evidence/m4/second-active-refused.jpg) |
| Draft/old balance | Closing while US-002 has a saved draft is refused. Publishing it then submitting the old balance produces a recoverable stale-membership refusal with decisions retained | [Draft refusal](evidence/m4/closure-draft-refused.jpg), [stale balance](evidence/m4/closure-stale-refused.jpg) |
| Closure and replay | Fresh balance carries US-001 to Sprint 2, returns US-002 to backlog and clears finished US-003. A second tab submits the same closure and receives the existing result | [Decisions](evidence/m4/closure-decisions.jpg), runtime snapshot |
| History stability | US-001 is later renamed and completed in active Sprint 2. Sprint 1 still shows its original title/`in_progress`; US-002's closed row stays `ready` while its current revision is `backlog` | [Current story](evidence/m4/current-story-desktop.jpg), [closed snapshot](evidence/m4/snapshot-before-withdrawal.jpg), runtime |
| Withdrawal | Archiving US-003 replaces its reader snapshot row with an unavailable marker; admin history keeps the original title, owner, applications and `done` state | [Reader withdrawal](evidence/m4/snapshot-withdrawal.jpg), [admin history](evidence/m4/snapshot-admin-history.jpg) |
| Closed state | Attempting to restore Sprint 1's old planned revision is refused without changing its closed publication/snapshot | [Reopening refusal](evidence/m4/closed-reopen-refused.jpg) |
| Responsible reader | The member attributed as sprint/story owner signs in as a reader, sees no admin controls and is denied direct closure/history access | [History denied](evidence/m4/reader-history-denied.jpg), runtime owner role remains `user` |
| Lists and home | Epic + backlog story filters return US-002. The closed snapshot's PLA filter returns only the visible matching row. Home highlights active Sprint 2 | [Home desktop](evidence/m4/active-home-desktop.jpg), browser notes |
| Responsive UI | Closed reader page, active home and new-story form observed at 390px with document width 390. Table remains in its scroll container; a keyboard Right input moves its horizontal position by 40px. Menu navigation works; final console warning/error capture is empty | [Closed desktop](evidence/m4/closed-reader-desktop.jpg), [closed mobile](evidence/m4/closed-reader-mobile.jpg), [home mobile](evidence/m4/active-home-mobile.jpg), [form mobile](evidence/m4/story-form-mobile.jpg) |

[Browser observation notes](evidence/m4/browser.json) describe the manual sequence. Snapshot triggers are installed and listed in the runtime evidence; direct SQL attempts to corrupt history were not run.

## Implementation corrections and limits

- An inactive responsible member already saved in a draft remains visible in the form for explicit reassignment. Publication still enforces active-member assignment rules; deactivation during draft editing was not separately exercised.
- Generic reader backlinks previously assumed only M3 kinds; epics/stories/sprints now return to their own lists. Closed administration explains its immutable state and omits the ordinary edit action.
- Restoration can now surface M4 validation errors as a preserved French form response, including refusal to reopen a closed sprint.
- The home page exposes the active sprint through a published-only projection. Optional archived links remain hidden; only required application/epic parents block archival, alongside the active-sprint lifecycle guard.
- Snapshot reader filters exclude unavailable story details, while admin history intentionally uses the complete preserved rows.

No automated domain test suite was added or run. Activation refusal was observed sequentially; this is not a simultaneous transaction race/load exercise. The shared account/project locks and singleton pointer guard implement serialization, but assembled concurrent acceptance remains M7. The 30-minute expiry boundary, every empty/cancelled sprint case, every archived-target combination, full keyboard/screen-reader matrix and closed-sprint archive/republication cycle were not exercised exhaustively. This checkpoint does not mark all SPEC-001 acceptance scenarios complete.

The existing upstream HTMX eval build warning remains; dynamic evaluation is disabled and CSP is unchanged. Real HTTPS/proxy/SMTP, deployment, backups and load behavior remain unqualified. Remote CI has not run, and no changes were committed or pushed during M4.

## Cleanup and next milestone

Inspection accounts are signed out, session credentials and temporary pipe metadata are removed, temporary browser tabs are closed and viewport overrides reset. Owned inspection services are stopped without deleting volumes. The normal development database is independently migrated to 25 migrations and remains empty of accounts, records and snapshots. [Normal database snapshot](evidence/m4/normal-database.json).

M5 is next: private file revisions, upload validation, preview jobs, every approved format adapter, original downloads and replacement/history. Preserve M0's source/adapter constraints and the M3 publication boundary. Search/chatbot remains M6 with its unresolved retrieval-quality gate; integrated acceptance and real-host adaptation remain M7.
