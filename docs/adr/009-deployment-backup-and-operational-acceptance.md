# ADR-009: Prepare explicit proxy trust and consistent private recovery before deployment

Status: accepted for operational preparation; provider qualification pending - Date: 2026-10-12

## Context

M7 must exercise the integrated private application and provide an operational handoff. Hosting, domain, SMTP and persistent storage are still “to be specified” by the owner on 2026-10-12. PostgreSQL metadata and private original/preview files must be recovered together. The public repository must not become a backup destination.

## Decision

- Supply a standalone production Compose reference using an immutable reviewed application image, a pinned PostgreSQL image, named private/database volumes, a one-shot migration service, web and worker. Do not start production until provider capabilities and acceptance conditions are confirmed.
- Keep PostgreSQL unexposed and bind the web upstream to loopback by default. Apply a non-root runtime, read-only web/worker roots, bounded temporary storage and initial CPU/memory/process limits. These limits are controls, not measured minimum hosting requirements.
- Require external private environment files and independent generated secrets. Keep deployment artifacts available for restore. Do not include environment secrets in database/file backup bundles; preserve them through a separate private recovery mechanism.
- Trust forwarding headers only from explicitly configured peer CIDRs. Reject default-route trust; require configured peers for HTTPS proxy mode. Accept one valid forwarded client address and valid forwarded scheme only from a trusted peer. Disable Gunicorn's independent forwarding inference. The actual proxy must overwrite client-supplied headers and be the only public path to the upstream.
- Preserve authenticated no-store behavior, CSP and secure cookies. Qualify domain-specific HSTS subdomain/preload choices rather than enabling flags solely to silence warnings. Redact bearer URLs and private identifiers at the proxy as well as in application logs.
- Use `audit_portal` as a read-only consistency/integrity inventory: migrations, current pointers/parents/passages, original and ready asset hashes, queue/lease state and ordered fingerprints of application tables. Full real inventories remain private; public evidence is limited to sanitized fictional summaries.
- Use the host-side `operations.py` CLI to back up PostgreSQL custom-format dump, private volume and audit/manifest together. Stop web/worker for consistency, refuse a running migration service, and resume only services that were running. The operator must stop unknown external writers and serialize backup/deploy/cleanup work.
- Verify bundle sizes/hashes before restoration. Restore only into a fresh `ubsi-restore-*` project with the exact backup image, no public ports, disabled SMTP and no web/worker startup. Refuse an existing project/volume/network and unsafe archive paths/links. Compare database table fingerprints and file/asset inventory; stop the copy while retaining its volumes for inspection.
- Report seven daily and four weekly retention points and expired candidates without automatically deleting them. Hosting must provide scheduling, encrypted off-host storage, monitoring and periodic recovery drills. Checksums alone do not provide encryption/authenticity or off-host resilience.
- Keep integrated technical acceptance, local load measurement, business retrieval qualification and real-host launch acceptance distinct. Retain failed/saturation observations separately; qualify baseline load without backup/restore contention and measure representative contention independently.
- Keep portal CI separate from the existing Release exporter. Portal changes trigger framework/build/isolated PostgreSQL acceptance and a reference image build; they never publish private data or deploy the application automatically.

## Alternatives considered

- Backing up a live database and copying files at unrelated times can create an inconsistent restore point.
- Restoring over an existing project risks destroying data before the backup is proven recoverable.
- Trusting all forwarded headers lets callers spoof source addresses/TLS origin and undermine rate limits.
- Committing dumps, private inventories or secrets into the source repository violates the private-data boundary.
- Assuming a small local corpus and fictional users validate a real provider's performance or the chatbot's answer quality overstates the evidence.

## Consequences and limits

Backups require a short maintenance window and sufficient free disk. The reference recovery uses the saved schema/image without silently migrating restored data. An update/rollback needs the matching artifact, a consistent pre-update point and explicit operator approval of the restored result.

M7 measured 46 local sessions, 50/50 successful admin preview requests in ten five-request batches, and an isolated restoration matching 32 table fingerprints and 25 originals. Those observations do not establish real-host recovery objectives, off-host protection, accessibility completion or retrieval quality. Provider details, representative files, assistive-technology review and owner-supplied M6 questions remain open. No production rollout is recorded.

## Evidence

[M7 report and acceptance matrix](../qualification/M7-integrated-acceptance-and-operations.md), [operations runbook](../operations/PORTAL-RUNBOOK.md), `portal/compose.production.yaml`, `portal/scripts/operations.py`, `portal/core/middleware.py`, operational management commands and `.github/workflows/portal.yml`.
