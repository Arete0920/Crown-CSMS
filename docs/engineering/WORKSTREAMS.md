# CROWN Active Workstream Register

This register provides a stable map of active repository work. GitHub issues and pull requests remain the live authority for status.

## Repository and governance

| Workstream | Issue | Current objective | Entry condition | Exit evidence |
| --- | --- | --- | --- | --- |
| Repository stabilization | #1343 | Clean, understandable, buyer-defensible repository | Canonical repository and documentation authority established | Independent clean-clone and handoff validation |
| CI architecture | #1337 | Inventory, consolidate, and contain workflow execution | Workflow-to-proof matrix complete | Stable canonical checks and retired duplicates |
| Ownership and attribution | #1354 | Record ownership, contributors, and human review | Human review in progress | Approved and merged governance record |
| Release truth | #1355 | Correct canonical status facts | Current main and provider direction verified | Approved and merged canonical status |
| Team collaboration | #1356 | Establish access, work ownership, and communication model | Verified usernames and working agreement | Collaborators onboarded and domain ownership assigned |

## Runtime architecture

| Workstream | Issue | Current objective | Required design artifact | Exit evidence |
| --- | --- | --- | --- | --- |
| Frontend API client | #1351 | One API base resolver and authenticated client | ADR and consumer inventory | Source guard and integration tests |
| Tenant enforcement | #1352 | One tenant-resolution and enforcement contract | ADR and middleware inventory | Tenant regression matrix passes |
| Household/student model | #1353 | One canonical household, guardian, and student model | ADR, dependency inventory, migration plan | Rehearsed migration and reconciliation proof |

## Dashboard and release-visible evidence

| Workstream | Issue | Current objective | Exit evidence |
| --- | --- | --- | --- |
| Authenticated dashboard proof | #1274 | Prove school-admin, teacher, and parent live-data flows | Same-SHA browser, network, console, and provenance evidence |
| Tenant-context dashboard proof | #1287 | Prove tenant identity propagation | With/without tenant probes and browser evidence |
| Visual QA | #1276 | Review release-visible routes | Route matrix with no unexplained console/network failures |

## Operations, security, and payments

| Workstream | Issue | Current objective | Exit evidence |
| --- | --- | --- | --- |
| Recovery and rollback | #1270 | Prove failed-deploy recovery and restore path | Controlled drill and accepted RTO/RPO |
| Secret-store readiness | #1294 | Move production secrets to approved external management | Identity-based access and configuration evidence |
| Rotation and break glass | #1296 | Establish operational secret controls | Approved runbook and drill evidence |
| Payment providers | #1298 | Prove CompuWerx and Metro readiness | Contract, credential, webhook, settlement, and security evidence |

## Release reconciliation

| Workstream | Issue | Current objective | Entry condition | Exit evidence |
| --- | --- | --- | --- | --- |
| Final release authority | #1275 | Reconcile final production decision | All production blockers closed or explicitly deferred | Explicit Product Owner authorization |
| Release documentation | #1277 | Refresh changelog, release notes, and runbooks | Runtime and operational evidence settled | Current same-SHA release packet |

## Work-in-progress rules

- Do not start implementation without an owning issue.
- Do not combine unrelated workstreams in one pull request.
- Keep no more than three active implementation pull requests under normal conditions.
- Design and inventory work may proceed while an implementation lane is under review, provided it does not modify overlapping runtime files.
- Documentation and GitHub issue-template changes are non-runtime work and must not be treated as runtime certification evidence.
- Update this register only when the workstream map changes; use issues and pull requests for daily status.
