# Azure runtime priority closure

Status: execution checklist; production acceptance remains NOT VERIFIED until the
current evidence satisfies each row. This document adds no release authority.
Follow `docs/CURRENT_RELEASE_STATUS.md`, the selected release's controlled
verification packet, and `docs/operations/PRODUCTION_RECOVERY_PATH.md`.

## Collect once, inspect through the connector

After the reviewed changes merge, manually run **Azure Classroom Release
Preflight** on `main`. PR and push runs test the collectors without Azure access.
The authenticated job retains three seven-day evidence artifacts:

- `azure-classroom-preflight-<sha>`: scoped resources and API configuration names.
- `azure-runtime-inventory-<sha>`: names-only settings across App Services,
  configured images and registry digest resolution, projected PostgreSQL backup
  metadata, and a bounded `/api/health/` observation.
- `azure-cost-diagnostics-<sha>`: fixed error categories for subscription cost and
  budget reads. No account IDs, resource names, monetary amounts, or raw provider
  messages are included in this diagnostic artifact.

The resource artifacts contain operational topology and must be handled under
existing repository access controls. No setting values, connection strings,
startup commands, database credentials, or health response bodies are retained.
Private billing output is deleted before artifact upload and again during cleanup.
Collection issues remain UNAVAILABLE; an empty list is not substituted for a denied
read. A failed HTTP observation is not sufficient to diagnose an outage.

## Evidence required to close each priority

| Priority | Read-only evidence | Required operational proof before closure |
| --- | --- | --- |
| Worker, beat, broker | App names, image references/digests, setting names, existing resource inventory | Identify the actual hosted worker and beat processes and broker endpoint in controlled storage; prove connectivity, registered task execution, and beat publication matched to worker execution by task ID. Check VMs and external services if Azure App Services do not identify these processes. |
| Database and classroom | API health's valid build SHA and database probe; exact source/deployment identity | Run the selected release's controlled migration verification against the correct hosted database, prove no pending required migrations, and exercise teacher/student/parent/admin/board permitted and denied actions with authorized test accounts. Verify persistence, retry behavior, and duplicate suppression. |
| Cost and budgets | Fixed provider error categories, explicit subscription query scope, existing inventory/tier reads | Diagnose actual live failures. Compare effective access scope with subscription cost/budget query scope. Correct the specific cause through the governed access or query path, then obtain successful scoped reads. Resource-group access is not evidence of subscription-wide access. Unknown costs remain unknown; budget absence is not inferred from an unavailable read. |
| Recovery | Configured image and registry manifest digest; PostgreSQL retention, redundancy, earliest restore metadata | Establish a prior successful compatible immutable image, current backup/restore point, isolated restore with schema/tenant/application checks, cleanup, measured RTO/RPO, and accepted rollback evidence for the selected identity. Provider backup metadata and fixture drills alone do not satisfy this row. |

Retain timestamp, source SHA, workflow run/job IDs, deployed identity, evidence
references, actual outcome, and unresolved gaps in the selected release packet.
Do not publish credentials, family/student records, monetary values, or private
provider diagnostics. Close tracked work only after its required evidence passes;
implementation, CI, merge, collection, deployment, and acceptance are separate states.

## Boundaries for the next action

The preflight performs reads only. It does not enqueue tasks, run migrations,
restart applications, create resources, change IAM, restore a database, deploy an
image, or authorize production cutover. Use the existing governed operational
workflows when their prerequisites are met. Do not run a production rollback drill
solely to produce a green check on a healthy service.

The repository's isolated PostgreSQL fixture drill validates restore mechanics.
Current production backup recovery still needs the operational proof above.
Planning targets and acceptance requirements remain those in
`docs/operations/PRODUCTION_RECOVERY_PATH.md`; this checklist does not change them.

## Provider references

- [Cost Management access and scope](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/assign-access-acm-data)
- [ACR repository/image attributes](https://learn.microsoft.com/en-us/cli/azure/acr/repository?view=azure-cli-latest)
- [PostgreSQL backup and restore](https://learn.microsoft.com/en-us/azure/postgresql/backup-restore/concepts-backup-restore)

The digest read resolves the configured registry reference at collection time; it
does not attest to the image digest inside an already running container. Health
`build_sha` is application-reported identity, not independent image attestation.
