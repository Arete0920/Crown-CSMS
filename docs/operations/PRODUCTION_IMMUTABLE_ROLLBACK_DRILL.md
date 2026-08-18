# Production Immutable Rollback Drill

**Status:** Runnable mechanics; current authorized operational execution evidence outstanding  
**Last authority reconciliation:** 2026-08-18  
**Current authority:** `docs/CURRENT_RELEASE_STATUS.md` plus the authorized owner-handoff/operational-transfer record for the selected exact identity  
**Historical trackers:** predecessor recovery issue numbers and release campaigns are provenance only  
**Production mutation:** Authorized execution only

## Freshness boundary

Before this runbook is used operationally, verify the exact current Crown-CSMS source/release identity, deployed runtime identity, container registry/repository, workflow definition, production environment, rollback target, database compatibility, credentials, protected-environment authority, and whether a later canonical runbook supersedes this one.

Earlier mechanics targeted Azure App Service `crown-api-prod` and Azure Container Registry path `crownregistry.azurecr.io/crown2026`. Those identifiers are historical mechanics context, not proof of the current successor production environment. Do not mutate any environment until its identity and authority are independently confirmed for the selected transfer/release.

## Purpose

This runbook provides the controlled manual path for proving application rollback from one known immutable release SHA to a prior known-good immutable image SHA.

It uses `.github/workflows/prod-immutable-rollback-drill.yml`, which applies the repository's immutable-image recovery mechanism. The workflow source proves runnable mechanics; it does not prove that a current operational drill occurred.

This runbook does not authorize a database restore, prove operational-backup recovery, establish accepted RTO/RPO commitments, authorize production deployment, or complete owner turnover.

## Required authority and access

The operator must have:

- explicit production release, transfer, or incident authority for the selected environment;
- permission to dispatch the approved GitHub Actions workflow;
- approval for the applicable protected production environment;
- current authorized cloud/OIDC credentials and permissions;
- authority to change the selected runtime's immutable image configuration and application settings;
- a preselected prior successful immutable image SHA known to be compatible with the current database state.

Stop if any authority, credential, environment identity, rollback target, or compatibility assumption is uncertain.

## Preconditions

Before dispatching the workflow, record:

1. the exact current Crown-CSMS source/release SHA;
2. the exact deployed runtime SHA expected to be live;
3. the prior successful immutable SHA selected as the rollback target;
4. the deployment/run or other immutable evidence establishing each runtime identity;
5. confirmation that the rollback SHA image remains present in the authorized container registry;
6. the operator, approver, UTC start time, and incident or drill reference;
7. confirmation that application rollback is safe against the current database schema and data state; and
8. the current owner-handoff/operational-transfer record that will retain the result.

The current and rollback SHAs must be different full lowercase 40-character commit SHAs. Mutable image tags such as `latest` are prohibited for proof.

## Abort criteria

Do not mutate production when:

- the approved runtime-health endpoint does not pass before the drill;
- pre-drill database status is not healthy;
- the live `build_sha` or equivalent immutable runtime identity does not equal the operator-supplied expected live SHA;
- the rollback image is absent from the authorized registry;
- schema or data compatibility is uncertain;
- production environment approval is absent;
- any required cloud credential or permission fails;
- the target environment cannot be proven to be the authorized production environment; or
- a separate active incident makes the drill unsafe.

If the workflow fails after mutation, treat the event as a production incident and follow `PRODUCTION_RECOVERY_DECISION_TREE.md`.

## Execution

1. Open **Actions** in the current Crown-CSMS repository.
2. Select **Production Immutable Rollback Drill**.
3. Select **Run workflow** from the controlling branch containing the approved workflow.
4. Enter the workflow's required exact identity and confirmation inputs, including the expected live SHA and rollback SHA.
5. Obtain protected-environment approval where configured.
6. Observe the workflow through all stages without cancelling it unless incident authority directs otherwise.

The workflow is expected to:

- validate explicit confirmation inputs;
- authenticate to the selected cloud environment through the approved mechanism;
- verify pre-rollback runtime health, database health, and exact live identity;
- prove the immutable rollback image exists in the authorized registry;
- configure the runtime to the exact SHA-tagged image;
- align the runtime build identity setting where applicable;
- restart or recycle the runtime as required;
- poll the approved health path until health, database status, and exact rollback identity are all proven;
- record operator, workflow run ID, timestamps, target identities, and elapsed seconds; and
- upload a retained evidence artifact.

## PASS criteria

The application rollback drill passes only when:

- the pre-rollback runtime exactly matches the recorded expected live SHA;
- the selected immutable rollback image exists under the full rollback SHA;
- the cloud/runtime platform accepts the immutable image configuration and restart/recycle;
- the approved runtime-health path passes after rollback;
- database status is healthy;
- the returned `build_sha` or equivalent immutable runtime identity exactly equals the rollback SHA;
- the evidence artifact is retained and referenced by the current owner-handoff/operational-transfer record; and
- measured elapsed time is reviewed against the currently accepted application rollback objective, if one has been established.

A green workflow alone does not complete operational acceptance. The authorized release/transfer authority must review identity, compatibility, elapsed time, operator record, evidence integrity, and any follow-up findings.

## Evidence to retain

Retain the GitHub workflow URL and the workflow's immutable evidence artifact. The retained packet should include, when available:

- exact Crown-CSMS source/release identity;
- pre-rollback runtime health and identity evidence;
- immutable rollback image reference;
- post-rollback verification attempts;
- final health result;
- UTC start and end timestamps;
- measured elapsed seconds;
- operator and approval identity;
- expected live SHA and rollback SHA;
- deviations, findings, and disposition; and
- reference to the authorized current transfer/release record.

Do not use predecessor issue numbers as the current evidence authority.

## Failure and escalation

Classify the result as `MANUAL CONTROL REQUIRED` when:

- the expected live SHA cannot be verified;
- the rollback image cannot be found;
- cloud configuration or runtime restart fails;
- the runtime does not become healthy within the approved retry window;
- database status is not healthy;
- live runtime identity does not equal the rollback SHA;
- environment or operator authority cannot be proven; or
- evidence is incomplete or contradictory.

Do not initiate database restore solely because application rollback failed. Database recovery requires the separate isolated/operational restore procedure and explicit authorization.

## Current release and transfer consequence

The repository contains a guarded executable application-rollback mechanism. That establishes **runnable mechanics**, not current operational execution proof.

Current operational rollback acceptance remains outstanding until an authorized drill or incident execution is tied to the exact selected Crown-CSMS release/runtime identity and retained in the current owner-handoff/operational-transfer record. Repository engineering/release posture remains governed by `docs/CURRENT_RELEASE_STATUS.md`; this runbook does not independently set a repository GO/NO-GO decision.
