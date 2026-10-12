# ADR-008: Return current source excerpts and gate reader retrieval on reviewed qualification

Status: accepted for the source and activation contract; ranking candidate experimental - Date: 2026-10-12

## Context

The chatbot must direct members to existing answers or refer them to urbanists. M0 established CPU feasibility but both measured ranking policies failed the required quality targets. ADR-004 rejects those policies as final behavior. M6 implements a new candidate; the owner explicitly chose to supply UBSI questions and expected answers before its qualification.

## Decision

- Keep general authenticated lexical search available independently of assistant qualification. Use current published records with reference/type/application/epic/sprint filters. Reader search never exposes drafts, archived pages or superseded publications.
- Restrict the assistant corpus to current published FAQ, epics, user stories and specification sections. Imported file bytes, account information, drafts and history are excluded. Derive exact section passages from the same canonical text used for reader pages.
- Commit lexical replacement/withdrawal and semantic jobs with publication/archive. Keep semantic chunks tied to record, revision and pinned model/index version. Recheck current eligibility before installing an index and before returning sources. Pending required current indexing causes technical unavailability; an old index is never a substitute.
- Use offline pinned multilingual E5 embeddings plus a multilingual cross-encoder on CPU as an **experimental** hybrid candidate. Artifact hashes/revisions live in `search/assets.lock.json`; thresholds, chunking and candidate counts live in `search/policy.py`. Do not describe these thresholds as calibrated or the candidate as accepted.
- Return at most one exact stored excerpt in the current candidate, with reference/title/section and a signed link to the current revision. This stays within SPEC-001's upper bound of three sources. Do not synthesize a free-form answer. Source routes and destination pages reject replaced or archived links.
- Separate no-answer fallback, qualification pending, invalid input, throttling and technical unavailability. The no-answer message is exactly: “Aucune réponse adaptée n’a été trouvée. Allez en parler aux urbanistes.” No message or ticket is sent to urbanists automatically.
- Bound questions to 500 characters and model token limits. Keep chat exchanges in page memory only, with clear/reset behavior. Do not persist transcripts or questions in diagnostic logs. Enforce per-account limits, five global leased retrieval slots and a per-process model lock with a four-second bounded wait.
- Leave reader retrieval disabled until an operator supplies a private qualification report inside private storage. Admin preview is explicitly experimental and cannot approve itself. The report must match the policy/model/implementation fingerprint, urbanist-reviewed expectations, frozen policy before held-out evaluation, at least 30 calibration cases, 30 independent cases and the 60 retained M0 regressions.
- Require at least 90% correct destinations on answerable held-out/regression cases and no returned incorrect/private/stale destination, together with lifecycle checks. Preserve abstention cases. Never use held-out questions to tune a candidate and then claim that same run independent.
- Invalidate activation when the fingerprint changes. Warm qualified models at process startup and fail readiness if the qualified model is unavailable. A successful local load run or source-card demonstration does not constitute business qualification.

## Alternatives considered

- Hosted generative answers add cost, data transfers and unsupported text beyond the requested source-direction behavior.
- Shipping the failed M0 policies or approving the candidate from a few manually selected examples contradicts the required qualification.
- Serving historical embeddings while indexing new publications risks redirecting users to obsolete answers.
- Adding a vector database now adds infrastructure before the bounded initial corpus demonstrates a need; exact CPU ranking is sufficient to evaluate the current candidate.

## Consequences and limits

Reader pages/FAQ/search remain useful while the assistant is pending qualification. Admins can inspect integration behavior without enabling reader responses. The report validates its declared evidence and fingerprint; the operator and urbanists remain responsible for the truth and independence of the recorded review/results.

General conflict detection, paraphrase adequacy and abstention quality remain unproven. Local fictional-data response times establish only engineering feasibility. No accepted reader activation report exists at this checkpoint. Future ranking changes require fresh independent qualification, while preserving the source/permission contract.

## Evidence

[M0](../qualification/M0-technical-qualification.md), [M6](../qualification/M6-search-and-chatbot.md), [M7](../qualification/M7-integrated-acceptance-and-operations.md), [review intake and retained regressions](../../qualification/m6/README.md). Implementation: `portal/search/`, `portal/frontend/assistant.ts` and `portal/templates/search/`.
