# Production Immutable Rollback Drill

**Status:** Runnable mechanics; operational execution evidence outstanding  
**Controlling lane:** GitHub issue `#1627`  
**Environment:** Azure production App Service `crown-api-prod`  
**Registry:** `crownregistry.azurecr.io/crown2026`  
**Effective date:** 2026-07-31  
**Last reviewed:** 2026-07-31

## Purpose

This runbook provides the controlled manual path for proving application rollback from one known production SHA to a prior known-good immutable image SHA.

It uses `.github/workflows/prod-immutable-rollback-drill.yml`, which applies the same immutable-image recovery mechanism already used by `.github/workflows/prod-rollback-on-failure.yml`.

This runbook does not authorize a database restore, prove database-backup recovery, establish accepted RTO/RPO commitments, close Lane 3, or approve production.

## Required authority and access

The operator must have:

- explicit production release or incident authority;
- permission to dispatch GitHub Actions workflows;
- approval for the protected `production` GitHub environment;
- working Azure OIDC secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`;
- authority to change App Service container configuration and application settings;
- a preselected prior successful immutable production image SHA.

Stop if any authority, credential, environment identity, or rollback target is uncertain.

## Preconditions

Before dispatching the workflow, record:

1. the current immutable release SHA expected to be live;
2. the prior successful immutable SHA selected as the rollback target;
3. the production deployment run that established each SHA;
4. confirmation that the rollback SHA image remains present in Azure Container Registry;
5. the operator, approver, UTC start time, and incident or drill reference;
6. confirmation that application rollback is safe against the current database schema and data state.

The current and rollback SHAs must be different full lowercase 40-character commit SHAs. The mutable `latest` tag is prohibited.

## Abort criteria

Do not mutate production when:

- `/api/health/` does not return HTTP 200 before the drill;
- pre-drill database status is not `ok`;
- the live `build_sha` does not equal the operator-supplied expected live SHA;
- the rollback image is absent from Azure Container Registry;
- schema or data compatibility is uncertain;
- production environment approval is absent;
- any required Azure credential or permission fails;
- a separate active incident makes the drill unsafe.

If the workflow fails after mutation, treat the event as a production incident and follow `PRODUCTION_RECOVERY_DECISION_TREE.md`.

## Execution

1. Open **Actions** in GitHub.
2. Select **Production Immutable Rollback Drill**.
3. Select **Run workflow** from the controlling branch containing the approved workflow.
4. Enter:
   - `expected_live_sha`: the exact full SHA currently expected in production;
   - `rollback_sha`: the exact prior known-good full SHA;
   - `confirm_environment`: `production`;
   - `confirm_action`: `ROLLBACK`.
5. Obtain protected-environment approval.
6. Observe the workflow through all stages without cancelling it unless incident authority directs otherwise.

The workflow will:

- validate explicit confirmation inputs;
- authenticate to Azure through OIDC;
- verify pre-rollback HTTP health, database health, and exact live SHA;
- prove the immutable rollback image exists in ACR;
- configure App Service to the exact SHA-tagged image;
- align the production `BUILD_SHA` application setting;
- restart App Service;
- poll `/api/health/` until HTTP 200, `db=ok`, and exact `build_sha` equality are all proven;
- record operator, workflow run ID, timestamps, target identities, and elapsed seconds;
- upload a retained evidence artifact.

## PASS criteria

The application rollback drill passes only when:

- the pre-rollback runtime exactly matches `expected_live_sha`;
- the selected ACR image exists under the full `rollback_sha` tag;
- Azure accepts the immutable image configuration and restart;
- `/api/health/` returns HTTP 200 after rollback;
- the returned database status is `ok`;
- the returned `build_sha` exactly equals `rollback_sha`;
- the evidence artifact is retained and linked to issue `#1627` and parent issue `#1619`;
- measured elapsed time is reviewed against the provisional 30-minute application rollback target.

A green workflow alone does not close Lane 3. Release authority must review the evidence, compatibility, elapsed time, operator record, and any follow-up findings.

## Evidence to retain

Retain the GitHub workflow URL and the artifact named:

`production-rollback-drill-<workflow-run-id>`

The artifact includes, when available:

- pre-rollback health JSON and summary;
- immutable rollback image reference;
- post-rollback verification attempts;
- final health JSON;
- UTC start and end timestamps;
- measured elapsed seconds;
- operator identity;
- expected live SHA and rollback SHA.

Record the artifact ID and digest in issue `#1627`.

## Failure and escalation

Classify the result as `MANUAL CONTROL REQUIRED` when:

- the expected live SHA cannot be verified;
- the rollback image cannot be found;
- Azure configuration or restart fails;
- the runtime does not return HTTP 200 within the workflow retry window;
- database status is not `ok`;
- live `build_sha` does not equal the rollback SHA;
- evidence is incomplete or contradictory.

Do not initiate database restore solely because application rollback failed. Database recovery requires the separate isolated restore procedure and explicit authorization.

## Current release consequence

The repository now contains a guarded executable manual rollback path derived from the actual production deployment architecture. The drill remains **UNPROVEN** until it is executed against an authorized immutable release identity and its operational evidence is accepted.

Production remains **NOT APPROVED / NO-GO / HOLD**.
