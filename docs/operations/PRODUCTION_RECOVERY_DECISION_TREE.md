# Production Recovery Decision Tree

**Authority:** Founder/Product Owner and production release governance  
**Status:** Release-blocking operational control  
**Related issue:** #1270

## Purpose

This document defines the required response when a production deployment fails or the live runtime cannot be verified. It does not claim that rollback or database restore has been proven. A controlled rollback drill and current restore evidence remain required before production approval.

## Governing principles

1. Deploy and recover by immutable 40-character image SHA.
2. Never treat the mutable `latest` tag as recovery evidence.
3. Do not mutate production when the live runtime is already healthy and its identity is verified.
4. A recovery is successful only when HTTP health, database health, configured image identity, application `BUILD_SHA`, and live `build_sha` agree.
5. Failed or incomplete verification is a manual-control incident, not a successful rollback.
6. Database restore is a separate decision from application-image rollback.

## Decision tree

### 1. Detect deployment failure

Capture:

- failed workflow name and run ID;
- candidate commit SHA and deployment tag;
- failure stage;
- current Azure-configured image;
- current application setting `BUILD_SHA`;
- `/api/health/` response;
- `/api/integrity/` response, including tenant-aware evidence where configured.

### 2. Recheck the live runtime before rollback

Do not roll back when all of the following are true:

- `/api/health/` returns HTTP 200;
- `db=ok`;
- the live `build_sha` is present;
- Azure's configured immutable image SHA, application setting `BUILD_SHA`, and live `build_sha` represent the same release;
- required integrity probes pass.

When these conditions pass, classify the workflow failure as a deployment-control or runner failure and open an incident for the failed control. Do not disturb the healthy runtime.

### 3. Select rollback candidate

When the live runtime is unhealthy or identity cannot be verified:

1. Find the newest prior successful production deployment from an authorized production workflow.
2. Require a full 40-character commit SHA.
3. Exclude the failed candidate SHA.
4. Verify that the exact SHA-tagged image exists in Azure Container Registry.
5. Stop and require manual intervention when no verified immutable candidate exists.

The `latest` tag must not be selected as a rollback source.

### 4. Perform application-image rollback

Restore only the verified immutable image:

`crownregistry.azurecr.io/crown2026:<40-character-sha>`

Align the production `BUILD_SHA` application setting to that same full SHA and restart the application through the approved production workflow.

### 5. Verify rollback

Rollback passes only when all required checks succeed:

- Azure reports the expected immutable image SHA;
- application setting `BUILD_SHA` equals the expected SHA;
- `/api/health/` returns HTTP 200;
- `db=ok`;
- live `build_sha` exactly identifies the expected release;
- tenant-aware integrity verification passes where configured.

Record the source deployment run, restored SHA, timestamps, verification output, and elapsed time.

### 6. Decide whether database restore is required

Do not restore the database solely because application deployment failed.

Escalate to database-restore evaluation when any of these conditions exist:

- migrations or application behavior caused confirmed destructive or incompatible data changes;
- database health remains failed after a verified application-image rollback;
- integrity checks show persistent data corruption or tenant-isolation failure;
- the application cannot operate safely against the current database state;
- the incident commander or Founder/Product Owner explicitly authorizes restore evaluation.

Before restore, capture current evidence, identify the approved backup, document expected data loss, and record the proposed recovery point.

### 7. Database restore fallback

A restore may proceed only through an approved, evidenced procedure with:

- verified backup identity and timestamp;
- documented recovery point objective impact;
- documented recovery time objective tracking;
- explicit production authorization;
- post-restore health, release-identity, schema, and tenant-integrity verification.

A restore is not complete until the restored database and the selected immutable application image are proven compatible.

### 8. Manual intervention triggers

Stop automation and open or update a production incident when:

- no prior successful immutable image exists;
- the registry does not contain the selected SHA tag;
- Azure image identity cannot be determined;
- health or database status remains failed after rollback;
- configured image SHA, `BUILD_SHA`, and live `build_sha` disagree;
- tenant-integrity verification fails;
- rollback workflow credentials or permissions fail;
- database restore may be required;
- any evidence is incomplete or contradictory.

## Evidence requirements

Each drill or real recovery must retain:

- UTC start and end timestamps;
- triggering workflow and run ID;
- failed candidate SHA;
- selected recovery SHA and its successful source run;
- registry existence proof;
- Azure configured-image proof;
- `BUILD_SHA` proof;
- health and database response;
- integrity response;
- rollback duration;
- restore duration when applicable;
- actual and target RTO/RPO notes;
- final classification: `RECOVERED`, `NOT RECOVERED`, or `MANUAL CONTROL REQUIRED`.

## Current release consequence

Until a controlled rollback drill and current database-restore evidence are recorded, production recovery remains unproven and issue #1270 remains open. No production-ready, pilot-start, or GO claim may rely on this document alone.