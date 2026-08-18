# Production Recovery Path

**Status:** Active recovery control; transaction-time production recovery evidence remains separately required.  
**Current authority:** `docs/CURRENT_RELEASE_STATUS.md` plus the authorized owner-handoff/operational-transfer record for the selected release or transfer identity.  
**Historical note:** predecessor recovery issue numbers are provenance only and are not current Crown-CSMS execution authority.

## Verified control state

The earlier rollback defect ran recovery after any upstream failure, including failures before Azure mutation. The current immutable rollback workflow supersedes that behavior. It rechecks live health, skips rollback when production remains healthy, resolves a prior successful full deployment SHA, verifies that exact image in Azure Container Registry, restores it, aligns `BUILD_SHA`, and verifies runtime identity and database health.

The dispatchable recovery-control drill tests decision logic without Azure access or production mutation. It is useful control evidence, but it is not an application rollback or database restore.

Historical rollback evidence proves that an earlier deployment path could restore a prior image. It is not current-release proof and does not satisfy current transaction-time recovery evidence by itself.

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

These are planning targets until a current drill records measured results and the authorized parties accept them.

## Current acceptance conditions

Final operational handoff or release must either contain current evidence for the selected exact identity or an explicit authorized residual-risk disposition covering:

- rollback decision-control and immutable-image behavior;
- current application rollback or explicitly approved equivalent evidence;
- current isolated restore evidence, including required tenant/application validation or an explicitly approved substitute;
- measured RTO/RPO results where required;
- exact source/deployment/runtime identity reconciliation;
- retained evidence linked to the current transfer/release record.

Repository recovery mechanics do not by themselves establish production deployment, production authorization, or completed owner turnover.
