# Production Recovery Path

Status: ACTIVE CONTROL / PRODUCTION RECOVERY NOT YET PROVEN

Controlling issue: #1270

## Current control state

The earlier rollback failure pattern was caused by a deploy-workflow step that ran after any prior failure, including failures before Azure mutation, and then exited unsuccessfully without restoring a prior image or configuration.

That implementation has been superseded:

- PR #1378 added an immutable application rollback workflow that rechecks live health, skips rollback when the runtime remains healthy, resolves a prior successful 40-character deployment SHA, verifies the exact image exists in Azure Container Registry, restores that image, aligns `BUILD_SHA`, and verifies HTTP health, database health, and exact live release identity.
- PR #1401 added a dispatchable, non-destructive recovery-control drill that exercises the decision logic and emits timestamped JSON and Markdown evidence without accessing Azure or mutating production.

These controls materially improve the recovery path, but they do not by themselves prove an actual Azure rollback or database restore. Issue #1270 remains open.

## Recovery decision tree

### 1. Failure before deployment mutation

Examples: input validation, freeze-window guard, authentication, build, dependency installation, security scan, preflight checks, or tests.

Required action:

1. Stop the failed deployment workflow.
2. Record the original failed step, run ID, candidate SHA, and logs.
3. Recheck production health and release identity.
4. When production is healthy and identity is verified, do not roll back.
5. Classify the event as a deployment-control failure and correct it before another attempt.

### 2. Failure after application image or app settings changed

Examples: health failure, tenant-integrity failure, `BUILD_SHA` mismatch, or release-identity mismatch after deployment mutation.

Required action:

1. Freeze further deployments.
2. Capture the failed SHA, current Azure image reference, app settings, health payload, integrity payload, and prior successful deployment evidence.
3. Invoke the approved immutable rollback path.
4. Restore only a verified prior 40-character SHA-tagged image.
5. Verify Azure image identity, `BUILD_SHA`, `/api/health/`, database health, live `build_sha`, and tenant-aware integrity.
6. Record timing, source run, selected SHA, restored image, and final disposition.

Rollback is successful only when the expected immutable identity and all required health and integrity checks agree.

### 3. Database-impacting failure

Evaluate database restore only when one or more of these conditions exist:

- a migration partially applied or cannot be safely reversed;
- integrity evidence indicates corruption or cross-tenant contamination;
- application rollback does not restore safe operation;
- database health remains failed;
- the application is incompatible with the current database state;
- the Founder/Product Owner or incident authority explicitly authorizes restore evaluation.

Required action:

1. Stop application writes where operationally possible.
2. Preserve logs and identify the proposed recovery point.
3. Verify the backup identity and timestamp.
4. Restore to an isolated validation target first when supported.
5. Validate schema, tenant isolation, critical record counts, release compatibility, and application health.
6. Record actual data-loss exposure and elapsed recovery time.
7. Obtain explicit authorization before any production restore or cutover.

### 4. Manual intervention triggers

Stop automation and enter manual incident control when:

- no prior successful immutable image exists;
- the selected SHA image is absent from the registry;
- Azure configuration or identity cannot be verified;
- rollback credentials or permissions fail;
- health, database, release identity, or tenant integrity remains failed;
- database restore may be required;
- recovery exceeds the pilot planning target;
- evidence is incomplete or contradictory.

## Required evidence

Every drill or real recovery must retain:

- UTC start and end timestamps;
- triggering workflow and run ID;
- failure stage and whether production mutation occurred;
- failed candidate SHA;
- pre-recovery live SHA and image reference;
- selected immutable recovery SHA and source deployment run;
- registry existence proof;
- Azure configured-image and `BUILD_SHA` proof;
- health, database, integrity, and tenant-probe results;
- rollback and restore duration where applicable;
- backup identifier and recovery point where applicable;
- operator and approving authority;
- final classification: `RECOVERED`, `NOT RECOVERED`, or `MANUAL CONTROL REQUIRED`.

## Pilot RTO/RPO planning targets

The following are planning targets for the controlled pilot drill, not approved or achieved service commitments:

- application rollback RTO target: 30 minutes from confirmed unhealthy runtime to verified restored identity and health;
- database restore validation RTO target: 4 hours from restore authorization to isolated validation completion;
- database RPO target: 24 hours maximum data-loss exposure for pilot planning, subject to verification of actual backup cadence and retention.

The drill must record measured results. Release authority must explicitly accept or revise these targets before they can be represented as approved controls.

## Closure conditions

Issue #1270 may close only when all of the following are evidence-complete:

- rollback failure root cause documented;
- immutable rollback implementation merged and validated;
- recovery-control drill executed with retained evidence;
- controlled Azure rollback or approved equivalent evidence recorded;
- current isolated database restore evidence or explicitly approved substitute recorded;
- measured RTO/RPO results documented;
- final evidence linked into the release-authority record.

Release posture remains: `CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED`.