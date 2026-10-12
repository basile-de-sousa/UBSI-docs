# M2 — Private access

Date: 2026-10-11

Status: implemented and observed locally on `main`. Real hosting, SMTP delivery and release acceptance remain outside this local checkpoint.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md). Setup and operator commands: [portal README](../../portal/README.md).

## Delivered

- French email/password sign-in, POST sign-out, invitation acceptance, recovery request and reset forms. No public registration or automatic account seed.
- Interactive `bootstrap_admin`, restricted to an empty directory. Passwords are hidden terminal input, validated and hashed with Argon2; no shared credentials or credential arguments.
- Admin directory, invitation/resend, role changes and account deactivation. Invitation email is fixed during acceptance; existing accounts cannot be recreated through an invitation.
- Single-use 72-hour random invitation secrets, stored as SHA-256 digests. Resend replaces the previous secret only when sending succeeds. One-hour reset tokens use Django's generator with administrative revocation included.
- Private views by default, active-session enforcement, fresh role lookup and server-side admin restrictions. Signed-out page requests redirect without copying private URLs; the private API returns 401. File/history authorization stubs precede M5. The assistant remains unavailable before M6.
- Twelve-hour database sessions. Deactivation increments a session access version so reactivation cannot revive old sessions. Password recovery also invalidates old sessions. Safe local redirects and CSRF protection remain enforced.
- PostgreSQL counters with expiring HMAC keys, source/account limits and 429/Retry-After responses. `REMOTE_ADDR` is the source; untrusted forwarding headers are ignored. `purge_access_state` removes expired counters and sessions.
- A shared row lock serializes account lifecycle writes and first/last-admin decisions. Per-account management versions reject stale forms. Accounts are deactivated rather than deleted.
- Stable UUID identity retained from M1; a provider/subject association model prepares future GitHub sign-in without exposing OAuth or automatic identity linking.
- Explicit optional development Mailpit sink in `compose.dev.yaml`, pinned by version/digest, loopback-only ports, no forwarding or persistent mailbox volume. This variant disables debug pages. No new Python/browser dependency.

## Local observations

The owner explicitly authorized fictional accounts in the separate Compose project `ubsi-portal-m2-preview`. Only synthetic display names and `example.invalid` addresses were used. No real message was sent. The normal development database was migrated independently and was not populated with these identities: [18 migrations, zero accounts](evidence/m2/normal-database.json).

| Area | Observed result | Evidence |
| --- | --- | --- |
| Build and schema | Native frontend types/build and Linux ARM64 image build completed. PostgreSQL 17.11 has 18 applied migrations, one account-control row and no pending migration/drift | [Framework checks](evidence/m2/django-checks.log), [frontend build](evidence/m2/frontend-build.log), [runtime](evidence/m2/runtime.json) |
| Signed out | Project/admin/file preview/original/history routes redirect to `/auth/login/`; assistant POST returns generic JSON 401; liveness/readiness return 200. Dynamic responses retain private/no-store and CSP headers | [HTTP observations](evidence/m2/public-http.json) |
| Bootstrap and admin | Interactive first-admin creation succeeded; admin sign-in opened the directory. Last-active-admin demotion was refused. Existing-member invitation returned a clear existing-account result | [Browser observations](evidence/m2/browser.json), [directory](evidence/m2/accounts-desktop.jpg), [last-admin refusal](evidence/m2/last-admin.jpg) |
| Invitation | Local mail captured; resend invalidated the prior claim. Form displayed the fixed email/assigned role at a clean URL. Application service accepted the invitation once; the used link was subsequently refused | Browser observations; runtime has one consumed invitation and two synthetic accounts |
| Reader and roles | Reader navigation omitted admin controls. Direct admin GET, stale admin POST and administrative file history were refused. Service promotion appeared in the existing session; UI self-demotion removed admin access | [Reader view](evidence/m2/reader.jpg), [refusal](evidence/m2/reader-denied.jpg), browser observations |
| Deactivation | Service deactivation followed by reactivation before the next browser request still revoked the old reader session; the same UUID was retained | [Revoked session](evidence/m2/session-revoked.jpg), runtime access version 2 |
| Recovery | Known/unknown addresses produced identical acknowledgement. Mail captured; clean reset form inspected. Application service changed the synthetic password, revoking the existing reader session; the used reset claim was refused | [Reset form](evidence/m2/reset-form.jpg), browser observations |
| SMTP outage | Mailpit stopped: invitation displayed a useful failure and left neither invitation nor account in the database. Known/unknown recovery addresses produced identical transport-failure text | [Failure screen](evidence/m2/smtp-unavailable.jpg), runtime, [safe event codes](evidence/m2/safe-events.log) |
| Throttling | Five invalid attempts for one synthetic address showed the generic login error; the sixth displayed the wait notice and remaining fixed-window delay | [Throttle screen](evidence/m2/throttled.jpg), browser observations |
| CSRF and logging | Empty sign-in POST without cookie/token returned 403. Captured server logs contained event codes, with no raw request URL, token, recipient or SMTP exception | HTTP observations and safe event codes |
| Responsive UI | Directory at widths 1280 and 390 had matching document width, with no horizontal overflow. Mobile menu opened; Escape closed it and returned focus. Final captured console log was empty | [Mobile directory](evidence/m2/accounts-mobile.jpg), [login](evidence/m2/login-desktop.jpg), browser observations |
| Existing export | CSV conversion completed: applications 10 rows, donnees 0, flux 0 | [Export output](evidence/m2/csv-export.log) |

Credential setup during invitation acceptance and recovery used application services from the terminal. The corresponding browser forms were inspected without entering/submitting a new password. This evidence does not claim a full browser credential-creation/reset acceptance run. No automated domain test suite was added or run; concurrency, expiry boundaries and recipient-specific SMTP rejection were not exercised as a suite. File checks concern guards and empty stubs, not uploaded file contents or previews.

## Corrections made during implementation

- A blanket `no-referrer` on authentication forms caused WebKit to send `Origin: null`, correctly rejected by Django CSRF. Only bearer-link exchange responses now use `no-referrer`; clean forms use `same-origin`. Logout followed by login from `/auth/login/` succeeded after the correction. CSRF was not exempted or weakened.
- Empty Django logger handler lists still allowed Python's fallback handler to emit raw rejection URLs. Explicit `NullHandler` entries now discard those raw logs; useful SMTP/CSRF diagnostics are separate safe codes.
- The response-policy middleware wraps access/CSRF middleware so early refusals and redirects receive private/no-store and CSP headers too.

`check --deploy` with synthetic production settings returned two expected domain-policy warnings: W005 (HSTS subdomains) and W021 (preload). Both settings remain explicitly off until the hosting domain is known; ordinary Django checks report no issues. The existing upstream HTMX eval warning remains in the build; evaluation is disabled and CSP is unchanged.

## Operational limits and next milestone

Production host/proxy/SMTP and HTTPS cookie behavior are not qualified. Source limits can be shared by users behind a proxy until trusted peer mapping is configured. Recovery responses have the same public text/status for known and unknown addresses but are not claimed to have constant timing. Invitation sending is synchronous inside the transaction with a 10-second SMTP timeout: SMTP acceptance followed by a database commit failure can leave a received link invalid, requiring resend. Provider delivery, proxy URL redaction, scheduling, backups and assembled-release behavior remain M7 work.

The GitHub workflow has not run remotely and changes have not been pushed. M3 is next: revisioned applications, specifications and FAQ, draft/publication/archive/restore, visual editing and the one-time CSV application import. Epics/stories and sprint workflows, actual document delivery and chatbot retrieval retain their planned milestones. M0's failed retrieval policies remain rejected.

Inspection services are stopped after capture. The isolated fictional database/private volumes are retained separately from normal development volumes. Temporary credential scripts are removed; no credentials are delivered as defaults. The normal database remains empty of accounts for the owner's interactive bootstrap.
