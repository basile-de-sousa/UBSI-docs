# M7 — Integrated engineering acceptance and operations

Date: 2026-10-12

**Status: local engineering work delivered; final release acceptance remains open.** The owner explicitly requested M7 while M6 business qualification is still pending and reconfirmed that hosting is **to be specified**. Reader chatbot activation remains gated. No deployment, real email delivery, commit or push was performed.

Baseline: [SPEC-001](../specs/SPEC-001-project-knowledge-portal.md), [PLAN-001](../plans/PLAN-001-project-knowledge-portal.md), [M6 report](M6-search-and-chatbot.md). Operator handoff: [runbook](../operations/PORTAL-RUNBOOK.md), [French portal guide](../../portal/README.md).

## Delivered

- A reproducible PostgreSQL engineering acceptance suite using generated fictional identities/content/files in a separate `test_*` database, destroyed after the run. The M7 request authorizes these checks. The normal development database remains separate from the fictional demonstration.
- Coverage of private routes, role/CSRF checks, invitation expiry/replacement/single use, SMTP rollback, session revocation, preserved authorship, last-admin protection, publication/draft/history invariants, cross-application links, dependency cycles, sprint closure/carry-over and PostgreSQL immutability guards.
- Real local preview preparation and exact original delivery for all eleven approved extensions: draw.io/XML, XLSX/CSV, PlantUML aliases, PDF, PNG/JPG/JPEG and SVG. Formula caches, hidden sheets, failed replacements, missing previews, oversized uploads and original corruption have focused checks.
- Concurrent PostgreSQL checks for editing conflicts, one active sprint, last-admin demotion, worker claims and five retrieval slots. A separate worker process claims a real fictional preview job and exits abruptly; after advancing only that synthetic lease, another attempt completes it. A stale completion token cannot finalize a reclaimed attempt.
- A read-only `audit_portal` command checks retained file/ready-preview digests, publication pointers, required parents, passage eligibility and migration state. It reports job/lease counts and ordered SHA-256 fingerprints of application tables without exposing their row text.
- Private quiesced backups containing the database dump, private volume, inventory and checksummed manifest. Restore requires the exact image and a fresh isolated project, rejects existing targets, disables published ports/email/reader activation, compares all table and file fingerprints, then stops without deleting volumes. Retention reports seven daily/four weekly points to keep; provider scheduling, encryption and off-host transfer remain operational work.
- A production Compose reference with private PostgreSQL, loopback web binding, bounded resources and read-only application filesystems. Trusted proxy handling accepts overwritten single-client addresses/TLS headers only from configured peers. Gunicorn forwarding inference is disabled. A provider runbook covers configuration, rollout, backup, recovery, monitoring and rollback.
- The existing CI configuration now installs Java/Cairo and runs the isolated engineering suite. Remote CI was not executed.

## Actual results and evidence

### Engineering suite

**49 distinct checks pass:** 45 runtime checks and four host operations checks. The runtime run discovers 49, passes 45 and skips the four host-script cases because that script intentionally lives outside the image; those four pass separately on the host. [Container log](evidence/m7/container-acceptance.log), [host log](evidence/m7/host-operations-tests.log).

The image builds for Linux ARM64. Django configuration/migration checks pass with 30 migrations and no schema drift. A synthetic production configuration passes Django deployment checks; unsafe debug, wildcard proxy trust and placeholder-secret configurations are rejected. Production Compose parses without starting production services. CSV conversion still succeeds for the existing 10/0/0-row referentials. [Build/check metadata](evidence/m7/checks-build.log), [production check](evidence/m7/production-check.json), [deployment check output](evidence/m7/production-check.log), [Compose summary](evidence/m7/production-compose.json), [CSV export](evidence/m7/csv-export.log).

### Backup and restoration

The isolated demonstration retains two authorized fictional accounts, 35 records, 40 revisions, 25 original files and 11 current eligible passages. The integrity audit succeeds; the five deliberately failed M5 previews remain recorded. The temporary load accounts/sessions are removed. [Final safe audit summary](evidence/m7/audit-summary.json).

A completed private backup was restored into a new `ubsi-restore-*` project in **7.438 seconds**. All 32 application-table fingerprints, all 25 retained originals and all ready-preview asset inventories match the source, with 30 migrations and matching counts. The precise elapsed time and image are in the [restore result](evidence/m7/restore-local.json); the [backup summary](evidence/m7/backup-summary.json) records the 3.322-second quiesced window and artifact sizes. Reusing an existing restore target is refused. The backing artifacts and full inventories remain private outside the checkout; no database dump or credential is published in this evidence directory. The rehearsal confirms local consistency, not provider recovery time or independent off-host recovery.

### Local HTTP measurements

The load command creates 46 temporary fictional sessions, warms the paths, then performs 138 requests per ordinary route through the actual loopback Gunicorn service. It separately warms the model pair and submits ten batches of five concurrent admin experimental-preview requests. The final status counts are reported without discarding failures. Actual p95 values, maximums and status counts are retained in [the load result](evidence/m7/load-local.json).

The final local timing/status targets pass: ordinary/search p95 values are 0.279s / 1.361s / 0.335s for applications/search/documents (414 HTTP 200 responses); admin preview p95 is 2.253s with all 50 requests successful and a 2.936s maximum. This meets the local two/five-second bounds on the fictional corpus. These are loopback measurements on the development machine, with ten five-request chatbot batches. They are **not** reader business-quality results, a statistically broad performance study, a network/browser rendering measurement or a promise for the future host. The reader gate was never bypassed.

### Browser and keyboard observations

The existing fictional reader signed in and out normally. Search, assistant and workbook pages remain within a measured 320px viewport; search was also observed at 390 and 1280px. The mobile menu opens with Enter, closes with Escape and restores focus. An observed skip-link defect was corrected: its target now receives focus as `MAIN#main`. Search submits with Enter, and the hidden workbook sheet remains selectable/readable with its label. Final browser error logs are empty. [Browser notes](evidence/m7/browser.json), [desktop](evidence/m7/search-reader-desktop.jpg), [320px search](evidence/m7/search-reader-320.jpg), [320px workbook](evidence/m7/workbook-reader-320.jpg).

Final anonymous HTTP observations return 200 for liveness/readiness, clean login redirects for private pages and 401 for assistant APIs, with private no-store headers. [HTTP evidence](evidence/m7/public-http.json).

The browser automation's arrow commands did not change native worksheet selection or table scroll state during this M7 pass. Worksheet switching was confirmed through the supported select control API. Hardware keyboard, screen reader, wider browser/device coverage and those native arrow interactions remain pending; they are not counted as passed here. M5's separate keyboard-scrolling observation remains historical evidence, not a substitute for that review.

## SPEC-001 acceptance matrix

“Covered locally” below means the stated synthetic engineering coverage; final business/provider acceptance remains separate. Earlier browser observations are linked from the milestone reports.

| Scenario | Local evidence / remaining acceptance |
| --- | --- |
| AC-01 private pages/files | Covered locally: anonymous redirects/API denial; no private response body |
| AC-02 reader writes | Covered locally: direct HTTP and service writes refused without mutation |
| AC-03 cross-application epic | Covered locally: the same epic appears under both applications |
| AC-04 story relationships | Covered locally: parent/app subset and required criteria validated |
| AC-05 publication separation | Covered locally: drafts leave reader text and eligible passages unchanged |
| AC-06 rejected publication | Covered locally: validation refuses publication and retains draft |
| AC-07 draw.io | Covered locally: two-page native/XML preparation, private preview response and exact download; M5 viewer observation retained |
| AC-08 workbook | Covered locally: worksheet manifest, hidden sheet, reader preview and exact original; browser worksheet consultation observed |
| AC-09 diagram formats | Covered locally: all approved aliases/formats prepare and deliver; representative real UBSI sources still needed |
| AC-10 chatbot correct source | **Pending M6 urbanist dataset and independent business qualification**; transport/current-source guards are engineering coverage only |
| AC-11 chatbot fallback | **Pending M6 business qualification**; draft exclusion, technical failure and qualification gate covered locally |
| AC-12 withdrawal | Current passage/source-link removal covered locally; M5 original/archive and M6 replacement observations retained; chatbot quality still pending |
| AC-13 invitation | Covered locally: assigned role, single use, expired and replaced invitations |
| AC-14 deactivation | Covered locally: session loses access and historical author identity remains |
| AC-15 sprint closure | Covered locally: atomic close, explicit carry-over and ambiguous-draft refusal |
| AC-16 concurrent editing | Covered locally: simultaneous saves yield one save and one conflict; recoverable UI observed in M3 |
| AC-17 restoration/history | Covered locally: text/file restores create drafts, current publication remains, reader history denied |
| AC-18 sprint snapshot | Covered locally: later story publication leaves closed membership/work state unchanged |
| AC-19 formula caches | Covered locally: numeric/empty/missing caches, no recalculation; browser saved values observed |
| AC-20 editor structures | Canonical headings/lists/tables/code and stable renamed heading IDs covered; full visual save/render observed in M3 |
| AC-21 import failure/limits | Covered locally: missing/failed previews, oversize source and failed replacement preserve the current original; wider representative limits retained from M0/M5 |
| AC-22 required parent | Covered locally: archive refused without broken published relationships |

## Corrections and scope limits

- The first native file-preparation checks encountered missing Cairo on this host. Those checks were moved to the planned Linux image with Java/Cairo; missing dependencies were not hidden or the assertions weakened. The public `/` route was correctly treated as the login form in the harness.
- An early concurrent test fixture omitted the required job source and failed the database constraint. It was replaced with an actual uploaded source. Thread connections are explicitly closed so test database teardown does not retain connections. These harness failures were corrected before the final passing run.
- The skip-link focus correction and trusted-proxy mapping are application changes found during M7. Proxy identity/TLS behavior still needs the actual provider's network/edge configuration.
- The abrupt-worker check advances an expired synthetic lease and covers claim/reclaim/completion. It does not reproduce every hard kill during Java rendering, storage exhaustion or all multi-host crash races.
- One earlier load run overlapped a restore rehearsal on the same Docker host and returned four successful preview requests and one HTTP 429. This [saturation observation](evidence/m7/load-during-restore.json) is retained. The bounded per-process model wait was increased from two to four seconds; final baseline measurements run after other checks/restoration stop, over ten batches rather than selecting one favorable batch. Real-host contention still requires qualification.
- Full source inventories and database fingerprints are private operational artifacts on a real deployment. The tracked evidence contains only fictional content and technical summaries. Generated user spreadsheets at repository root were not imported or edited.
- Synthetic production checks do not contact SMTP, provision HTTPS or launch the reference production stack. HSTS subdomain/preload policy is explicitly deferred to domain ownership; the positive check assumes a dedicated HTTPS-only domain.

## Remaining inputs before launch

1. Urbanist-approved UBSI question/answer/source cases, independent M6 evaluation and an accepted activation report.
2. Representative private UBSI files/content volumes and final editorial review; broader hardware keyboard/assistive-technology/browser checks.
3. Actual hosting capabilities, trusted proxy peers, domain/TLS, real invitation/recovery delivery, persistent storage and resource measurements.
4. Scheduled daily/weekly verified backups on an independent encrypted destination and a real-host restore rehearsal; operational ownership and final release acceptance.

These items keep M6 and final M7 acceptance open. The local work is reviewable now; no further clarification is needed to retain it safely.

## Teardown

Owned browser tabs/sessions are closed and viewport overrides reset. The isolated demonstration services and restore rehearsals are stopped without deleting data volumes. The normal development database remains empty and stopped. Private fictional backup points remain outside the repository for recovery. No real member was invited, no external email was sent, and no production endpoint was opened.
