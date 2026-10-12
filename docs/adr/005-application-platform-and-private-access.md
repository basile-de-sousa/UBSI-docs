# ADR-005: Use a Django/PostgreSQL application with private account services

Status: accepted for implementation - Date: 2026-10-12

## Context

[ADR-003](003-project-knowledge-portal.md) authorizes a private custom portal for 46 members. SPEC-001 requires controlled writes, explicit publication, private documents and invitation-only email/password accounts. The approved [implementation plan](../plans/PLAN-001-project-knowledge-portal.md) was executed through M1–M7. This ADR records the resulting platform and access decisions; it does not declare production hosting accepted.

## Decision

- Keep the portal in `portal/`, independently of CSV exports and the existing Release workflow. Use Python 3.12, Django 5.2, PostgreSQL 17, Gunicorn and server-rendered French templates. Exact versions, hashes and image digests are held in dependency locks and the Dockerfile.
- Bundle CSS, TypeScript, HTMX and Tiptap with Vite. Node is a build dependency; browsers load assets from the portal origin. Disable HTMX dynamic evaluation and received scripts; preserve the restrictive CSP. Use WhiteNoise only for built public assets.
- Use one web process with threads and one PostgreSQL-backed worker initially. Do not add a queue broker, vector service or frontend application server. Qualify combined resource use on the real host before changing process counts.
- Use a custom UUID `User`, normalized unique email, reader/admin role and active state. Prefer Argon2 through Django password APIs. Keep provider identity separate in `LoginIdentity`; no GitHub OAuth or implicit email-based linking is implemented.
- Expose invitation-only access, interactive first-account bootstrap, POST logout and recovery. No account/password is seeded. Invitations use random single-use secrets stored as digests, expire after 72 hours and are replaced on successful resend; recovery uses one-hour framework tokens.
- Use twelve-hour database sessions and recheck current account/role on requests. Increment the access version on deactivation so reactivation cannot revive old sessions. Password reset revokes previous sessions. Serialize account lifecycle writes with `AccountControl`; retain accounts referenced by history and protect the last active admin.
- Check administrator authorization again inside mutation services. UI visibility alone never grants authority. Use CSRF protection and safe local redirects. Anonymous private pages redirect to a clean login URL; private JSON APIs return 401.
- Store expiring rate counters in PostgreSQL using HMAC keys rather than raw submitted emails/source IPs. Keep useful safe event codes while suppressing raw bearer URLs and account/question text in application logs.
- Default configuration to production and reject debug mode, placeholder/short secrets, wildcard hosts and public/private storage overlap. Local Mailpit is explicitly opt-in and does not deliver real email. TLS/proxy mapping is recorded separately in [ADR-009](009-deployment-backup-and-operational-acceptance.md).

## Alternatives considered

- A static documentation site cannot implement the approved private writes, account lifecycle and authenticated file delivery.
- A separate SPA/API and queue broker add deployment components without a demonstrated need for this team size.
- SQLite would not exercise the PostgreSQL row-locking, full-text and trigger contracts used by the application.
- Public registration, a shared default administrator and role claims cached only in cookies conflict with controlled membership and prompt revocation.
- Immediate GitHub OAuth integration would expand the initial scope; a stable identity boundary preserves a later implementation path.

## Consequences and limits

The host must support persistent PostgreSQL/private volumes, a supervised Python web process/worker and the local Java/Cairo/model dependencies. Setup downloads pinned public artifacts; runtime inference does not call a hosted model service. The public source repository must never contain runtime accounts or uploaded files.

Synchronous SMTP inside account transactions can fail visibly and roll back invitations. SMTP acceptance followed by a database failure may leave a received link invalid; the admin resends. Equal recovery messages do not establish constant timing. Provider delivery, real HTTPS cookies and operational log redaction still require host qualification.

## Evidence

[M1](../qualification/M1-application-foundation.md), [M2](../qualification/M2-private-access.md) and [M7](../qualification/M7-integrated-acceptance-and-operations.md) record actual checks and their limits. Implementation: `portal/config/`, `portal/accounts/`, `portal/core/`, frontend locks and Compose files. Operating commands: [portal README](../../portal/README.md).
