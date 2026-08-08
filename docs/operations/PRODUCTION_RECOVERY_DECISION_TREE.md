# Production Recovery Decision Tree

**Authority:** Founder/Product Owner and production release governance  
**Status:** Canonical recovery procedure; full measured operational drill remains disclosed maturity work  
**Last reconciled:** 2026-08-08  
**Historical issue:** #1270 — closed  
**Current release authority:** `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue #1619

## Purpose

This document defines the required response when a production deployment fails or the live runtime cannot be verified. It reflects the immutable rollback implementation and non-destructive recovery controls already present in the repository.

It does **not** claim that the separately disclosed full application rollback and isolated operational-backup restore campaign has been executed with accepted measured RTO/RPO. That exercise remains visible in current diligence/handoff material as deferred operational maturity unless separately completed and accepted.

## Governing principles

1. Deploy and recover by immutable 40-character image SHA.
2. Never use the mutable `latest` tag as recovery authority.
3. Do not mutate production when the live runtime is healthy and its identity is verified.
4. A recovery passes only when image identity, `BUILD_SHA`, live `build_sha`, HTTP health, database health, and required integrity checks agree.
5. Incomplete or contradictory verification means `MANUAL CONTROL REQUIRED`.
6. Application rollback and database restore are separate decisions.
7. Planning targets are not approved service commitments until measured and accepted by the accountable authority.
8. Development `main` does not displace the certified production identity merely because later commits exist.

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
- version/release identity response;
- required tenant-aware integrity response.

### 2. Recheck the live runtime before rollback

Skip rollback when all required checks pass:

- `/api/health/` returns HTTP 200;
- database status is healthy;
- live `build_sha` is present;
- configured image SHA, `BUILD_SHA`, immutable release authority, and live identity reconcile as required for that deployment;
- required tenant-aware integrity probes pass.

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

Restore only an explicitly verified immutable image such as:

`crownregistry.azurecr.io/crown2026:<40-character-sha>`

Align the production `BUILD_SHA` setting to the same full SHA and restart through the approved rollback mechanism.

### 5. Verify application rollback

Rollback passes only when all required evidence succeeds:

- Azure reports the expected immutable image SHA;
- application setting `BUILD_SHA` equals the expected SHA;
- `/api/health/` returns HTTP 200;
- database status is healthy;
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
- documented expected RPO impact;
- RTO tracking;
- explicit authorization for the target environment;
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
- evidence is incomplete or contradictory.

## Evidence requirements

Each drill or real recovery should retain:

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

Do not retain secret values or customer personal data in the evidence packet.

## Planning targets

These remain planning targets until a measured exercise is explicitly accepted:

- application rollback RTO: 30 minutes;
- isolated database restore validation RTO: 4 hours;
- pilot database RPO: 24 hours maximum data-loss exposure, pending current backup-cadence verification.

They must not be represented as measured or contractually guaranteed values without current evidence.

## Current release consequence

The repository contains immutable rollback logic, recovery decision controls, isolated-restore tooling/runbooks, and recovery-evidence validation. The bounded certified production release itself is **PASS / COMPLETE** under the exact identity recorded in `docs/CURRENT_RELEASE_STATUS.md` and #1619.

The broader measured rollback/isolated-restore campaign remains an explicitly disclosed operational-maturity item. Its non-execution does not rewrite the certified release decision, and it must not be represented as completed until a separate measured exercise is performed and accepted.
