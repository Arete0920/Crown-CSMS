# DEV blacklist database inventory

This standalone read-only workflow is intentionally separate from draft PRs #352 and #365. After the workflow is accepted on protected main, dispatch **DEV Blacklist Database Inventory (read-only)** from main, with its full accepted source SHA.

The collector verifies accepted source ancestry, Azure DEV App Service identity and environment markers, and DEV PostgreSQL hostname. It uses TLS verification and a read-only, repeatable-read database transaction. It reads only blacklist migration names and schema metadata. It cannot apply migrations, modify application configuration, restart a web app, or authorize activation. Its JSON artifact expires in seven days.

Possible classifications: `CLEAN_UNINITIALIZED`, `VENDOR_HISTORY_AND_TABLES_PRESENT`, or `RECONCILIATION_REQUIRED`. A blocked read reports a fixed reason code. A clean result does not prove live runtime version, backups, or readiness to deploy.

Before activating the blacklist, independently verify current database migration history, the SimpleJWT vendor migration graph, backup/restore, required PostgreSQL tests, and the reviewed schema-before-traffic deployment sequence. Preserve the fail-closed migration gate; never fake migration records or expose credentials in CI artifacts.
The dispatcher requires the **exact current main SHA** (not an older accepted ancestor). It uses its own concurrency group, so it cannot cancel an in-flight DEV deployment. Inventory reflects a read-only point-in-time database observation, not a proof that the deployed code was unchanged before or after collection. Review any overlapping DEV deployment before treating evidence as release authority.
