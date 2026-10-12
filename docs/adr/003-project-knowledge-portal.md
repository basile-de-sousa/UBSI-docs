# ADR-003: Build a private project knowledge portal

Status: accepted - Date: 2026-10-11

## Context

UBSI members need a shared place to consult applications, epics, user stories, sprints, written specifications, data flow diagrams, spreadsheets, database diagrams and FAQ answers. Administrators need to maintain and publish these records. Readers need read-only consultation and a chatbot that directs them to existing published answers or refers them to urbanists.

ADR-002 selected GitHub Releases instead of a website for document distribution. The project owner now explicitly requests a custom website, beginning with detailed specifications and followed by an implementation plan. This decision replaces ADR-002's no-website policy; it does not require removing existing download workflows.

## Decision

- Build a private UBSI knowledge portal with reader and administrator roles.
- Use invitation-only email/password accounts initially, preserving a future path to GitHub authentication.
- Organize content by application, with cross-application epics, user stories and shared project sprints.
- Provide editable specification pages and imported documents with previews and original downloads.
- Require explicit publication of drafts and subsequent changes.
- Use a visual specification editor, simple Excel previews and administrator-only version history with restoration into drafts and archiving.
- Limit initial sprint management to objectives, dates, stories, owners and work states, preserving an immutable record at closure.
- Limit chatbot sources to published FAQ and the written content of epics, user stories and specifications. Refer unanswered questions to urbanists using a message only.
- Size the initial deployment for the 46-member team without mandatory paid services. Hosting is provided; its capabilities remain to be specified in the implementation plan.
- Write and approve SPEC-001 before application implementation. Prepare the implementation plan after the specifications.
- Work directly on `main`, as requested. No framework, hosting service or chatbot technology is selected by this ADR.

## Consequences

- The earlier no-website policy no longer applies.
- Authentication, permissions, publication, file previews and knowledge retrieval require explicit specification and implementation.
- Private account information, uploaded documents and runtime data must not be committed to the public source repository.
- Existing CSV reference data and Release downloads remain available while import and synchronization responsibilities are specified.
- SPEC-001 was approved and marked `ready` on 2026-10-11. PLAN-001 records the implementation sequence and technical proposal; hosting capabilities remain to be qualified.
