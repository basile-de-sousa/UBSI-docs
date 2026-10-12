# ADR-006: Separate drafts from immutable publications and close sprints atomically

Status: accepted for implementation - Date: 2026-10-12

## Context

Readers must see explicitly published content while admins prepare edits. Applications, epics, stories, specifications, FAQ, documents and sprints share identity/history rules, but have different validation. Closed sprints must preserve what was actually completed or carried over. Concurrent administrators must not overwrite one another or close a changed backlog silently.

## Decision

- Represent stable identity with `ContentRecord` UUIDs and reserved, non-reused human references. Store one mutable `ContentDraft` separately from append-only `ContentRevision` rows. Reader projections start from the current published pointer, never from a draft.
- Store relationships as typed foreign-key rows, not arbitrary identifiers embedded in editor JSON. Preserve historical labels/revisions where needed, while canonical links resolve current published targets. Retain former application codes as reservations/aliases when publishing a rename.
- Centralize create/edit/save/publish/archive/restore/discard in services. Acquire the account-control lock, recheck admin access and acquire `ProjectState` before project mutations. Check expected edit versions; stale forms return a recoverable conflict.
- Publish a complete validated revision, its relations, current pointer, lexical passages and durable indexing job in one transaction. Draft edits/restoration never replace the current publication. Invalid publication leaves the saved draft available for correction.
- Validate required published parents, story application membership within its epic, dependency acyclicity, responsible accounts, ready file preparation and per-kind fields under the lock. Refuse archiving a required parent while current published dependents need it.
- Protect revision/relation immutability and pointer ownership with PostgreSQL triggers as well as service/model checks. Do not expose generic Django admin editing of these records. Restore history into a new draft rather than editing or deleting history.
- Persist visual editor content as allowlisted canonical JSON. Derive escaped reader HTML, exact text and passages through the same server schema. Retain heading UUIDs across title changes. Bound nodes/tables/text and reject active HTML, styles and unsafe links.
- Import `data/applications.csv` once through a bounded preview/confirmation workflow, creating drafts and an import receipt. Preserve existing codes and subsequent portal edits; do not synchronize automatically from Git or overwrite the directory on startup.
- Keep work state separate from publication state. Sprints are shared across applications, with at most one active sprint held by `ProjectState`. Activation requires published assignments and active owners.
- Close a sprint in one transaction: revalidate the displayed sprint/story/target versions, reject unresolved participating drafts, require an explicit disposition for every incomplete story, publish resulting assignments/states, close the sprint and store immutable pre-closure snapshot rows. Backlog clears the assignment and sets backlog state; carry-over preserves work state in a planned sprint. Finished/cancelled stories lose their current assignment. An identical retried closure returns its existing result.
- Show snapshot fields on a closed sprint even if current stories change. Canonical story links open the current story. Archived sources are withdrawn according to current visibility rules; historical preservation does not grant reader access to an archived page. Closed sprints cannot be reopened.

## Alternatives considered

- Overwriting a single content row makes drafts visible and destroys reliable history.
- JSON-only links weaken referential validation and make dependency queries difficult to protect.
- Fine-grained project locks could increase parallel writes but add lock-order complexity without a demonstrated need for this small administrator group. The shared project lock is an intentional tradeoff.
- Updating story assignments before snapshot creation records the next sprint instead of the closing sprint.
- Rebuilding closed sprints from current story fields makes past deliverables change after closure.

## Consequences and limits

Administrative writes serialize; readers continue using committed publications. PostgreSQL is part of the correctness contract. New content kinds must extend schema, relations, publication validation, projections and acceptance coverage together. Model migrations must preserve history triggers and existing immutable records.

This is record versioning with explicit workflows, not collaborative real-time editing or a general event-sourcing platform. Git CSV referentials and live portal content have distinct responsibilities after the one-time import.

## Evidence

[M3](../qualification/M3-revisioned-knowledge.md), [M4](../qualification/M4-backlog-and-sprints.md) and [M7](../qualification/M7-integrated-acceptance-and-operations.md), including simultaneous saves, sprint activation and direct-SQL guards. Implementation: `portal/knowledge/`, `portal/sprints/` and their migrations.
