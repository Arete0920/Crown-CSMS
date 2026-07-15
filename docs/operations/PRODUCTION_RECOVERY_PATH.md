# Production Recovery Path

Status: DRAFT CONTROL / PRODUCTION RECOVERY NOT YET PROVEN

Controlling issue: #1270

## Verified rollback failure root cause

The current production deploy workflow defines a step named `Rollback on failure` with `if: failure()`. That condition runs after any prior job failure, including failures that occur before `Deploy to Azure Web App`.

The step does not restore a prior image, prior app settings, a deployment slot, or a database backup. It prints that Azure will handle automatic rollback and then exits with status 1.

Consequences:

- pre-deploy test or guard failures are incorrectly reported as rollback failures even though no deployment mutation occurred;
- post-deploy verification failures do not trigger an actual restoration action;
- the workflow cannot distinguish `nothing changed` from `runtime changed and recovery required`;
- a failing rollback step obscures the original deployment failure.

This explains the observed pattern in production deploy run `29202250977`, where tests failed before Azure deployment, deployment steps were skipped, and the rollback step still failed.

## Existing evidence that must not be overstated

The February 23, 2026 tag-driven drill proved that a known-good commit can be redeployed and SHA-verified through the production deployment pipeline. That is useful historical evidence, but it does not prove that the current automated failure handler performs rollback or that database restore readiness is current.

## Recovery decision tree

### 1. Failure before deployment mutation

Examples: input validation, freeze-window guard, authentication, build, security scan, dependency installation, preflight checks, or tests.

Action:

1. Stop the workflow.
2. Record the original failed step and logs.
3. Do not invoke rollback because production was not changed.
4. Verify production health and release identity remain on the prior known-good SHA.
5. Correct the pre-deploy defect before another deployment attempt.

### 2. Failure after application image or app settings changed

Examples: BUILD_SHA mismatch, health failure, tenant-integrity failure, or release-identity mismatch after deployment.

Action:

1. Freeze further deployments.
2. Capture the failed deploy SHA, previously observed production SHA, Azure image configuration, app settings, health payload, and integrity payload.
3. Redeploy the prior known-good immutable SHA through the controlled production dispatch workflow.
4. Verify Azure image SHA, BUILD_SHA app setting, `/api/health/`, `/api/integrity/`, and expected tenant behavior.
5. Record start time, recovery-complete time, operator, commands, run IDs, and evidence paths.

This is a manual fallback until an automated rollback implementation is reviewed and proven.

### 3. Database-impacting failure

Trigger database restore review when any of the following is true:

- a migration partially applied or cannot be safely reversed;
- integrity checks indicate data corruption or cross-tenant contamination;
- application rollback does not restore service correctness;
- the database is unavailable or materially inconsistent.

Action:

1. Stop application writes where operationally possible.
2. Preserve logs and identify the recovery point.
3. Follow the approved database backup/restore procedure.
4. Restore into an isolated validation target first when supported.
5. Validate schema, tenant isolation, critical record counts, and application health before production cutover.
6. Record actual recovery point and elapsed time.

No database restore procedure is considered proven until a current drill or approved equivalent evidence is attached to #1270.

### 4. Manual intervention triggers

Escalate to manual incident control when:

- the prior immutable application image is unavailable;
- Azure configuration cannot be read or changed safely;
- rollback health checks fail;
- database recovery is required;
- expected tenant isolation cannot be verified;
- the recovery attempt exceeds the pilot RTO target;
- evidence is incomplete or contradictory.

## Evidence required for the controlled drill

Record all of the following:

- UTC start and end timestamps;
- initiating failure condition;
- pre-drill production SHA and image reference;
- failed candidate SHA;
- rollback or redeploy run ID;
- restored SHA and image reference;
- BUILD_SHA verification output;
- health and integrity verification output;
- tenant probe result;
- database backup identifier and recovery point, when applicable;
- operator and approver;
- measured recovery time;
- measured or demonstrated recovery point;
- final PASS or FAIL disposition.

## Pilot RTO/RPO controls

The pilot RTO and RPO remain `TBD / NOT APPROVED` until the drill records measured evidence and the release authority accepts the targets.

The drill must propose and validate explicit values. Planning assumptions must not be reported as achieved service levels.

## Closure conditions

This document alone does not close #1270. Closure still requires:

- workflow behavior that does not report rollback for pre-deploy failures;
- a fixed automated rollback or owner-approved manual fallback;
- a controlled failed-deploy or rollback drill;
- current database restore evidence or an explicitly approved substitute;
- measured RTO/RPO notes;
- evidence linked to #1270 and final release-authority reconciliation.

Release posture remains: `CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED`.
