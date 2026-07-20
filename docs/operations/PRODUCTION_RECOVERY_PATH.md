# Production Recovery Path

**Status:** Active control; current production recovery is not yet proven.  
**Controlling issue:** #1270

## Verified control state

The earlier rollback defect ran recovery after any upstream failure, including failures before Azure mutation. The current immutable rollback workflow supersedes that behavior. It rechecks live health, skips rollback when production remains healthy, resolves a prior successful full deployment SHA, verifies that exact image in Azure Container Registry, restores it, aligns `BUILD_SHA`, and verifies runtime identity and database health.

The dispatchable recovery-control drill tests decision logic without Azure access or production mutation. It is useful control evidence, but it is not an application rollback or database restore.

Historical February 23, 2026 tag-driven rollback evidence proves that an earlier deployment path could restore a prior image. It is not current-release proof and does not satisfy #1270 by itself.

## Decision tree

### Failure before production mutation

Stop the workflow, preserve the failed step and logs, recheck production health and identity, and do not roll back a healthy runtime. Correct the automation failure before another deployment attempt.

### Failure after application image or settings mutation

Freeze deployments, capture the failed and live SHAs, verify the prior successful immutable image, execute the approved rollback workflow, and prove exact image, `BUILD_SHA`, HTTP health, database health, and tenant integrity.

### Database-impacting failure

Enter manual incident control when a migration is partially applied, corruption or tenant contamination is suspected, application rollback cannot restore safe operation, or database health remains failed. Restore first to an isolated database. Validate backup age, archive readability, schema, required tables, migration history, tenant isolation, critical record counts, and application compatibility. Record measured recovery time and data-loss exposure. Production cutover requires explicit authorization.

## Current restore verifier

`python manage.py verify_backup_restore` is the repository control for isolated PostgreSQL restore validation. It must:

- refuse missing PostgreSQL client tools;
- refuse missing or stale backups outside `CROWN_RPO_HOURS`;
- preflight the archive with `pg_restore --list`;
- restore to a unique isolated database with fail-fast behavior;
- validate public tables, required table identifiers, and Django migration history;
- redact PostgreSQL credentials from command failures;
- emit timestamped JSON evidence including backup digest, age, elapsed time, and cleanup result;
- never mutate the production database.

Additional tenant and application checks remain required during the actual controlled drill.

## Planning targets

- application rollback RTO: 30 minutes;
- isolated database restore validation RTO: 4 hours;
- database RPO: 1 hour, aligned with `CROWN_RPO_HOURS`.

These are planning targets until a current drill records measured results and the Founder/Product Owner accepts them.

## Closure conditions

Issue #1270 remains open until all are complete:

- rollback root cause and current implementation are documented;
- decision-control simulation has retained evidence;
- current Azure rollback or explicitly approved equivalent evidence exists;
- current isolated restore evidence exists, including tenant/application validation or an explicitly approved substitute;
- measured RTO/RPO results are recorded;
- final evidence is linked into release authority.

Release posture: `CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED`.
