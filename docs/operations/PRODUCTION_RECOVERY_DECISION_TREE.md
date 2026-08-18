# Production Recovery Decision Tree

**Authority:** Founder/Product Owner and production release governance  
**Status:** Canonical recovery procedure; current operational execution evidence remains separately required  
**Last reconciled:** 2026-08-17  
**Current release authority:** `docs/CURRENT_RELEASE_STATUS.md` and Crown-CSMS issue #14

## Purpose

This document defines the required response when a production deployment fails or the live runtime cannot be verified. It reflects immutable rollback and non-destructive recovery controls present in the repository.

It does **not** claim that the current Crown-CSMS turnover release has completed an authorized immutable application rollback or operational-backup restore exercise with accepted measured RTO/RPO. Those are separate evidence gates.

## Governing principles

1. Deploy and recover by immutable 40-character image/source identity.
2. Never use a mutable `latest` tag as recovery authority.
3. Do not mutate production when the live runtime is healthy and its exact identity is verified.
4. A recovery passes only when image identity, `BUILD_SHA`, live `build_sha`, HTTP health, database health, and required integrity checks agree.
5. Incomplete or contradictory verification means `MANUAL CONTROL REQUIRED`.
6. Application rollback and database restore are separate decisions.
7. Planning targets are not approved service commitments until measured and accepted.
8. Repository `main` does not become a deployed production identity merely because it is current source authority.
9. Historical Crown2026 deployment evidence may identify prior known-good candidates only when exact compatibility and current operational authority are independently verified.

## Decision tree

### 1. Detect deployment failure

Capture the failed workflow/run, candidate SHA/tag, failure stage, mutation status, configured image, `BUILD_SHA`, health response, version/release identity, database status, and required tenant-aware integrity result.

### 2. Recheck live runtime before rollback

Skip rollback only when all required checks pass: HTTP health, database health, live build identity, configured image, application setting, release authority, and required tenant-integrity probes all reconcile for the expected deployment.

If these conditions pass, classify the event as a deployment-control failure and leave the healthy runtime unchanged.

### 3. Select an immutable rollback candidate

When the runtime is unhealthy or identity cannot be verified:

1. identify the newest prior successful **authorized and compatible** production deployment;
2. require its full immutable SHA;
3. exclude the failed candidate;
4. prove the exact SHA-tagged image exists in the configured container registry;
5. prove application/database schema compatibility for the candidate;
6. stop for manual control when no verified candidate exists.

The mutable `latest` tag must never be selected.

### 4. Perform application-image rollback

Use only the approved rollback workflow/mechanism and the exact verified image identity for the target environment. Align the production `BUILD_SHA` setting to the same full SHA and restart through the governed path.

### 5. Verify application rollback

Rollback passes only when the configured image, `BUILD_SHA`, live `build_sha`, HTTP health, database health, and required tenant/integrity verification all match the selected immutable recovery identity. Retain source deployment run, restored SHA, timestamps, elapsed time, outputs, operator/authority record, and final classification.

### 6. Decide whether database restore is required

Do not restore the database solely because application deployment failed. Escalate to restore evaluation only for confirmed destructive/incompatible data change, persistent database-health failure, integrity/corruption evidence, application/database incompatibility, or explicit incident authority.

### 7. Database restore fallback

A restore may proceed only through an approved procedure with verified backup identity/timestamp/digest, expected RPO impact, RTO tracking, authorized target, isolated validation where supported, and post-restore schema, tenant-isolation, record/integrity, compatibility, and health verification.

A restore is incomplete until the restored database and selected immutable application image are proven compatible.

### 8. Manual intervention triggers

Stop automation when no verified compatible rollback image exists, registry/image identity cannot be proven, credentials/permissions fail, health remains failed, source/image/runtime identities disagree, tenant/integrity verification fails, database restore may be required, or evidence is incomplete/contradictory.

## Evidence requirements

Each drill or real recovery should retain UTC timestamps, triggering workflow/run, failure stage/mutation status, failed candidate SHA, selected recovery SHA/source run, registry proof, configured-image proof, `BUILD_SHA`, health/database/integrity evidence, rollback duration, restore duration/backup identity where applicable, actual-vs-target RTO/RPO notes, operator/authority record, and final classification (`RECOVERED`, `NOT RECOVERED`, or `MANUAL CONTROL REQUIRED`).

Do not retain secret values or customer personal data in recovery evidence.

## Planning targets

Existing planning targets remain noncontractual until measured and explicitly accepted. Current canonical recovery/runbook documents govern the exact expected targets and procedure at execution time.

## Current turnover consequence

The repository contains rollback and isolated-restore mechanics and evidence-validation controls. **Current operational rollback/restore completion is not established merely by those controls existing.** The selected Crown-CSMS turnover release must have the required current execution evidence or an explicit authorized residual-risk disposition before final operational handoff is represented as complete.
