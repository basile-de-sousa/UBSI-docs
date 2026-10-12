# UBSI portal — Operations runbook

Status: M7 local engineering preparation. Hosting capabilities remain **to be specified** by the owner (2026-10-12). This is a deployment reference, not a record of production rollout. Reader chatbot acceptance remains blocked on the owner-supplied UBSI question/answer/source set.

## 1. Provider handoff

Record the operator, domain, TLS termination/proxy peer addresses, Linux CPU architecture, Docker/Compose versions, memory/CPU/disk allowance, private persistent storage, SMTP relay, encrypted off-host backup destination and maintenance window. Confirm outbound access required for artifact acquisition and SMTP; inference and document rendering use local assets.

Use an immutable application image built from the reviewed release source, including pinned viewers/models. The supplied Compose reference requires support for `!reset` when performing an isolated restore. Production secrets and environment files live outside the public checkout, mode 600, readable only by the responsible operator. Private data volumes and backups must not be served by the proxy or uploaded to GitHub Releases.

The Compose resource bounds are starting controls, not validated provider sizing. Re-run representative measurements on the supplied host: 46 sessions, five concurrent chatbot requests, ordinary/search p95 <2s and chatbot p95 <5s on warmed models. Record non-200 responses separately. Run a baseline without concurrent backup/restoration or acceptance jobs, then qualify representative contention independently rather than combining or discarding those results. Agree real representative content/file volumes before claiming these service targets.

## 2. Private environment

Start from the documented variable names in [`.env.example`](../../portal/.env.example), without using its placeholder secrets. Supply:

- `PORTAL_ENV_FILE`: absolute operator-controlled environment path; also pass this file with Compose `--env-file` for interpolation.
- `PORTAL_IMAGE`: immutable registry image digest, matching the reviewed build. Keep this artifact available for restoration/rollback.
- Generated `SECRET_KEY` (at least 50 characters), independent random PostgreSQL credentials, database name/user and SMTP credentials. The reference Compose URL interpolation requires a URL-safe database password; use a generated URL-safe value or adapt the URL construction explicitly.
- Explicit `ALLOWED_HOSTS`, including the public hostname and loopback health-probe host; `PUBLIC_BASE_URL=https://<actual-domain>`, matching HTTPS CSRF trusted origins and the real SMTP sender/transport.
- `TRUST_HTTPS_PROXY=true` only for an edge that **overwrites** forwarding headers; set `TRUSTED_PROXY_CIDRS` to actual proxy peers/networks, never `0.0.0.0/0` or `::/0`. Do not assume the Docker bridge address is constant. The middleware ignores forwarding headers from other peers and accepts only one valid forwarded client IP. Gunicorn forwarding inference is disabled so Django applies this peer check before TLS handling.
- Leave `CHATBOT_QUALIFICATION_FILE` unset until M6 business evidence is accepted. The activation report belongs inside private storage, is tied to the policy/code fingerprint and must accompany the exact approved artifacts.

The [production Compose reference](../../portal/compose.production.yaml) has no database port exposure and binds the application only on host loopback. Adapt that binding for a containerized proxy using a private network and firewall rules. The development Compose/mailpit files are not the production configuration.

## 3. Proxy requirements

Terminate HTTPS with a valid certificate; redirect public HTTP to HTTPS. Forward only the application route to the private web upstream. Overwrite `Host`, `X-Forwarded-Proto` and `X-Forwarded-For` with trusted values derived from the connection, not appended client headers. Set an upload request allowance slightly above the 20 MiB original-file bound to accommodate multipart overhead (for example 22 MiB); the application still enforces its own limit.

Do not cache authenticated HTML/APIs/files. Preserve CSP, no-store and cookie headers. Do not expose `/var/lib/ubsi/private`, database/model paths or worker controls. Keep upload buffering/temp storage private and bounded. Align proxy request timeouts with the bounded application requests; preview preparation remains asynchronous.

Disable raw request-URL/query/header/body logging on paths containing invitation/reset/source tokens. Operational access logs can contain status and timing without URLs or account identifiers. Inspect error-log behavior too: a sanitized application logger does not sanitize a proxy's raw upstream-error messages. Record the actual proxy configuration in the private deployment record.

## 4. Initial release

Run commands from the reviewed checkout. Replace `/private/ubsi.env` below with the actual operator path; it is a path, not a secret argument. Use the same project/configuration consistently.

```sh
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml pull
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml run --rm migrate python manage.py check --deploy --fail-level ERROR
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml up -d
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml exec web python manage.py bootstrap_admin
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml exec web python manage.py audit_portal
```

Bootstrap is interactive and first-account-only. Inspect live/readiness through the private upstream and through the actual HTTPS entry point. Verify private pages require login, reader writes fail, invitation/recovery emails reach authorized recipients, originals remain private and an ordinary supported import reaches ready. Perform the directory import as a dry run before applying it through the admin workflow. Real content is published explicitly by admins; there is no automatic repository-document migration.

Review every deployment warning. HSTS subdomain/preload flags require control of the actual domain and HTTPS on every affected subdomain; do not enable them blindly to suppress W005/W021. The local synthetic configuration check assumes a dedicated HTTPS-only domain and does not decide the real provider's policy.

M6 activation and launch approval are separate acceptance gates. An unqualified assistant page must continue to state that qualification is pending. Do not manufacture an activation report to pass readiness or a demonstration.

## 5. Consistent backups

The host script [operations.py](../../portal/scripts/operations.py) creates a PostgreSQL custom-format dump, the entire private volume, a read-only integrity inventory (including ordered fingerprints of all application tables) and SHA-256 manifest. The application environment file is **not** included: maintain secrets in the provider's separate recovery mechanism. Account/password hashes and private documents are included, so encrypt backups at rest and in transit and restrict access. Checksums establish integrity, not authenticity or encryption.

The script stops web/worker, refuses a running migration service, copies both stores during that maintenance window and resumes only services that were running. Other application instances, ad-hoc writers/imports and cleanup jobs must also be stopped by the operator; the script cannot fence unknown external writers. Never run a second backup, deployment, cleanup or restore concurrently. Reserve free disk space for the dump plus uncompressed private archive. The script streams archives rather than loading them into memory.

```sh
python3 portal/scripts/operations.py --project ubsi-portal-production --compose portal/compose.production.yaml --env-file /private/ubsi.env backup --destination /private/off-host-mounted-backups/ubsi --tier daily
python3 portal/scripts/operations.py --project ubsi-portal-production --compose portal/compose.production.yaml --env-file /private/ubsi.env verify --backup /private/off-host-mounted-backups/ubsi/<backup-id>
python3 portal/scripts/operations.py --project ubsi-portal-production --compose portal/compose.production.yaml --env-file /private/ubsi.env retention --destination /private/off-host-mounted-backups/ubsi
```

Use a mode-700 backup root outside the repository and live private volume. Only a completed valid manifest is restorable. A failed attempt leaves an incomplete directory for diagnosis and does not replace any earlier backup. The retention command reports the seven newest daily and four newest weekly points to keep, and candidates for operator removal; it never deletes files. Invalid/incomplete backups are not silently treated as valid restore points.

Configure the host scheduler after provider approval: daily backup in the agreed maintenance window and one weekly-tier backup each week. The local implementation does not install a scheduler. Copy completed verified points to an independent provider-approved encrypted destination; a backup on the application's live disk alone does not satisfy recovery requirements. Alert on command failure, missed daily backup, failed verification or insufficient restore points. Target data loss remains 24 hours; feasible recovery time is determined by the real-host rehearsal.

## 6. Restore rehearsal and incident recovery

Keep the release image/model artifacts and independently recoverable environment secrets. First verify the manifest, then restore into a **new** `ubsi-restore-*` project. The script refuses existing project containers, volumes or networks and never overwrites a live database. It removes published ports, disables account email transport and chatbot activation, starts only the isolated database, restores the private volume with safe regular-file/directory extraction, and compares migrations/counts/all retained original and ready-asset digests with the source inventory.

```sh
python3 portal/scripts/operations.py --project ubsi-restore-rehearsal --compose portal/compose.production.yaml --env-file /private/ubsi.env restore --backup /private/off-host-mounted-backups/ubsi/<backup-id>
```

It compares all table fingerprints as well as file inventories/counts, records elapsed time, then stops the rehearsal without deleting volumes. Use the same image as the backup; mismatched migrations/artifacts require a reviewed migration plan. An integrity rehearsal does not replace authenticated browser checks after recovery. The restored copy must remain isolated: it includes account sessions, invitation state and private content. Never expose it as a second public service or enable outbound email accidentally.

For a real incident: stop public writes, preserve the failing volumes, restore to a fresh isolated target, perform consistency and authenticated checks, then switch the proxy only after operator acceptance. Revoke restored sessions and pending invitations/reset proofs if the incident involves account compromise; rotate secrets through the provider mechanism and reissue access deliberately. Do not delete the prior volumes until recovery is accepted. Record actual downtime/data loss and recovery duration. Returning source code to an old commit alone is not a database/file rollback.

## 7. Daily operation and recovery of jobs

```sh
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml ps
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml exec web python manage.py audit_portal
docker compose --env-file /private/ubsi.env -f portal/compose.production.yaml exec web python manage.py search_status
```

Monitor readiness, disk/memory use, backup age, worker process/restarts, pending-job age, expired running leases and failed job counts. The audit emits technical counts/UUIDs/digests rather than text, emails or bearer tokens; keep its full inventory private on a real deployment. Deliberately failed unreferenced preparations do not themselves make the current site unavailable; investigate newly failed current imports/indexes via the admin interface.

Jobs have leases, fenced completion and bounded retries. Restart a failed worker with the same configuration; expired work is reclaimed after its lease. An admin preview retry or `reindex_search --actor UUID` never publishes data or qualifies the assistant. Inspect the cause before repeatedly retrying malformed/over-limit files. Run document cleanup in dry-run mode first and outside backup/deployment windows; it must retain all referenced originals/history.

Updates use an accepted release artifact, pre-migration consistent backup, serialized migration, readiness and short authenticated checks. Keep the matching previous artifact and backup until the update is accepted. The CI workflow is separate from the existing CSV/Release workflow and must not export private runtime material.

## 8. Acceptance and handover

Record results against all 22 SPEC-001 acceptance scenarios, including explicit pending/partial items. Local fictional-data engineering checks do not approve business answers or promise real-host latency. Complete the representative private-file/question matrix, keyboard/mobile and assistive-technology review, real email delivery, HTTPS/proxy mapping, off-host backups and restoration before launch. Future GitHub authentication remains outside this initial delivery.
