# Production Recovery Decision Tree

**Authority:** Founder/Product Owner and production release governance  
**Status:** Release-blocking operational control  
**Related issue:** #1270

## Purpose

This document defines the required response when a production deployment fails or the live runtime cannot be verified. It reflects the immutable rollback implementation merged in PR #1378 and the non-destructive recovery-control drill merged in PR #1401.

It does not claim that a controlled Azure rollback or database restore has been proven. Those evidence requirements remain open.

## Governing principles

1. Deploy and recover by immutable 40-character image SHA.
2. Never use the mutable `latest` tag as recovery authority.
3. Do not mutate production when the live runtime is healthy and its identity is verified.
4. A recovery passes only when image identity, `BUILD_SHA`, live `build_sha`, HTTP health, database health, and required integrity checks agree.
5. Incomplete or contradictory verification means `MANUAL CONTROL REQUIRED`.
6. Application rollback and database restore are separate decisions.
7. Planning targets are not approved service commitments until measured and accepted by release authority.

## Decision tree

### 1. Detect deployment failure

Capture:

- failed workflow name and run ID;
- candidate commit SHA and deployment tag;
- failure stage;
- whether Azure application configuration changed;
- current configured image;
- current application setting `BUILD_SHA`;
- `/api/health/` response;
- `/api/integrity/` response, including tenant-aware evidence where configured.

### 2. Recheck the live runtime before rollback

Skip rollback when all required checks pass:

- `/api/health/` returns HTTP 200;
- `db=ok`;
- live `build_sha` is present;
- configured image SHA, `BUILD_SHA`, and live `build_sha` identify the same release;
- required integrity probes pass.

When these conditions pass, classify the event as a deployment-control failure. Record the failed workflow and leave the healthy runtime unchanged.

### 3. Select an immutable rollback candidate

When the runtime is unhealthy or release identity cannot be verified:

1. Find the newest prior successful authorized production deployment.
2. Require a full 40-character commit SHA.
3. Exclude the failed candidate SHA.
4. Verify that the exact SHA-tagged image exists in Azure Container Registry.
5. Stop and require manual intervention when no verified immutable candidate exists.

The `latest` tag must never be selected.

### 4. Perform application-image rollback

Restore only:

`crownregistry.azurecr.io/crown2026:<40-character-sha>`

Align the production `BUILD_SHA` setting to the same full SHA and restart through the approved rollback workflow.

### 5. Verify application rollback

Rollback passes only when all required evidence succeeds:

- Azure reports the expected immutable image SHA;
- application setting `BUILD_SHA` equals the expected SHA;
- `/api/health/` returns HTTP 200;
- `db=ok`;
- live `build_sha` exactly identifies the expected release;
- tenant-aware integrity verification passes where configured.

Record the source deployment run, restored SHA, timestamps, elapsed time, verification outputs, and final classification.

### 6. Decide whether database restore is required

Do not restore the database solely because application deployment failed.

Escalate to restore evaluation when:

- migrations or application behavior caused confirmed destructive or incompatible data changes;
- database health remains failed after verified application rollback;
- integrity checks show persistent corruption or tenant-isolation failure;
- the application cannot operate safely against the current database state;
- incident authority explicitly authorizes restore evaluation.

Before restore, preserve current evidence, identify the approved backup, document expected data loss, and define the proposed recovery point.

### 7. Database restore fallback

A restore may proceed only through an approved, evidenced procedure with:

- verified backup identity and timestamp;
- documented RPO impact;
- documented RTO tracking;
- explicit production authorization;
- isolated validation where supported;
- post-restore schema, tenant-isolation, record-count, release-compatibility, and health verification.

A restore is incomplete until the restored database and selected immutable application image are proven compatible.

### 8. Manual intervention triggers

Stop automation and open or update a production incident when:

- no prior successful immutable image exists;
- the registry lacks the selected SHA tag;
- Azure image identity cannot be determined;
- rollback credentials or permissions fail;
- health or database status remains failed after rollback;
- configured image SHA, `BUILD_SHA`, and live `build_sha` disagree;
- tenant-integrity verification fails;
- database restore may be required;
- recovery exceeds the pilot planning target;
- evidence is incomplete or contradictory.

## Evidence requirements

Each drill or real recovery must retain:

- UTC start and end timestamps;
- triggering workflow and run ID;
- failure stage and mutation status;
- failed candidate SHA;
- selected recovery SHA and successful source run;
- registry existence proof;
- Azure configured-image proof;
- `BUILD_SHA` proof;
- health, database, integrity, and tenant evidence;
- rollback duration;
- restore duration and backup identity when applicable;
- actual and target RTO/RPO notes;
- final classification: `RECOVERED`, `NOT RECOVERED`, or `MANUAL CONTROL REQUIRED`.

## Pilot planning targets

These are provisional drill targets, not approved or achieved commitments:

- application rollback RTO: 30 minutes;
- isolated database restore validation RTO: 4 hours;
- pilot database RPO: 24 hours maximum data-loss exposure, pending backup-cadence verification.

Measured drill evidence and release-authority acceptance are required before these values can be represented as approved controls.

## Current release consequence

The current controls are stronger and now include immutable rollback logic plus a non-destructive decision drill. However, production recovery remains unproven until controlled Azure rollback evidence and current database-restore evidence are recorded.

Issue #1270 remains open. Production remains not approved.