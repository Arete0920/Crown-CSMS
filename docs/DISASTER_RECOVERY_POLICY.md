# CROWN Disaster Recovery Policy

**Status:** Active planning and control policy; current recovery capability is not yet production-certified.  
**Controlling issue:** #1270  
**Accountable authority:** Founder/Product Owner

## Recovery objectives

These are controlled-pilot planning targets, not achieved service-level commitments:

| Objective | Planning target | Evidence required |
| --- | ---: | --- |
| Application rollback RTO | 30 minutes | Measured immutable-image rollback from confirmed unhealthy state to exact-SHA healthy runtime |
| Isolated database restore validation RTO | 4 hours | Measured restore to a non-production validation database with structural and tenant checks |
| Database RPO | 1 hour | Current backup timestamp and retention evidence proving a usable recovery point within one hour |

The one-hour RPO matches `CROWN_RPO_HOURS` in application settings. A drill must fail when the selected backup is older than the configured RPO window. Any temporary exception requires explicit Founder/Product Owner acceptance and must not be represented as the normal control.

## Required backup evidence

Do not infer that backups exist from policy text. Each current drill must capture, with secret values excluded:

- backup source and immutable identifier;
- backup creation or last-modified timestamp;
- backup age at drill start;
- backup size and SHA-256 digest;
- configured retention and redundancy;
- exact application and database environment used for validation.

## Isolated restore procedure

1. Select a non-production backup that satisfies the configured RPO.
2. Run `pg_restore --list` to fail before database creation when the archive is unreadable.
3. Create a uniquely named isolated PostgreSQL database.
4. Restore with `pg_restore --exit-on-error --no-owner`.
5. Verify a minimum public-table count, required tables, and applied Django migrations.
6. Run tenant-isolation, critical-record-count, schema, and application-compatibility checks appropriate to the selected evidence set.
7. Record elapsed time and the measured recovery-point age.
8. Drop the isolated database unless a failed drill is intentionally preserved for investigation.
9. Obtain explicit authority before any production restore or cutover.

Command:

```bash
python manage.py verify_backup_restore \
  --backup-path /backups/latest.dump \
  --required-table core_school \
  --required-table core_useraccount \
  --evidence-path audit-artifacts/recovery/restore-evidence.json
```

The command proves only the checks it records. It does not by itself prove tenant isolation, application compatibility, production cutover, Azure backup configuration, or production readiness.

## Application rollback

Use the immutable rollback workflow only after the live runtime is demonstrably unhealthy or unavailable. A failed deployment with a healthy runtime is an automation incident and must not trigger a needless rollback.

A successful rollback requires agreement among:

- a prior successful 40-character deployment SHA;
- availability of the exact SHA-tagged image in Azure Container Registry;
- Azure configured image identity;
- `BUILD_SHA`;
- HTTP and database health;
- live `build_sha` and required tenant-integrity checks.

## Drill cadence and retained evidence

Run at least quarterly and before production authorization after material recovery-path changes. Retain UTC start/end time, operator, approver, source run, selected image or backup, measured RTO/RPO, validation output, cleanup result, and final disposition.

## Closure rule

Policy, code, dry runs, simulations, and historical drills do not close #1270. Closure requires current application rollback evidence or an explicitly approved substitute, current isolated database restore evidence, measured results, and linkage into release authority. Production remains not approved until that evidence is accepted.
