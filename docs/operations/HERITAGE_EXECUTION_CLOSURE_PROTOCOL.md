# CROWN execution and closure protocol

**Authority:** Owner direction, 2026-10-18. Applies to Heritage Azure completion and subsequent CROWN execution. This is an operational procedure, not evidence of completed deployment.

## Work queue (strict priority)

1. Release PR #316: strong isolated candidate-validation secrets; exact-head required checks; protected merge.
2. Release PR #318: sixth specialist persona in deployed Heritage certification; exact-head checks; protected merge.
3. Deploy accepted, immutable backend and Azure frontend artifacts; record source/build/image SHA and Azure resource identities.
4. Run authenticated, **deployed** Heritage certification: admin, teacher, parent, student, board, admissions specialist, across authorized tenant boundaries. Require real API persistence, permission denials, and provenance evidence.
5. Verify rollback, isolated restore, monitoring, credential rotation, and payment fail-closed boundary.
6. Issue sales walkthrough only after live certification, with current URLs, working access procedure, known restrictions, and dated evidence.

Do not declare a PR merged because CI passed, nor a deployment complete because a local rehearsal passed.

## Execution loop (every active work session)

1. Inspect the authoritative repository and relevant Azure runtime evidence once per exact SHA or meaningful state transition.
2. Select the highest-ranked executable task and identify its acceptance condition.
3. Execute the correction, run targeted tests, and enter governed CI/PR review.
4. **While blocked or waiting**, immediately execute another independent safe task from the queue; never substitute polling or status notes for available work.
5. When a gate completes: merge via protected controls, deploy only through authorized release mechanisms, and verify live identity and behavior.
6. For failures: gather logs, isolate root cause, implement and test a repair. Do not weaken gates, forge evidence, bypass branch protections, or repeat denied operations without a material change.
7. Record concrete outputs (SHA, PR, run, environment, test artifacts) and close only when every criterion is evidenced.
8. Give concise outcome-based reports, not a sequence of intentions. Explicitly distinguish incomplete tasks, unavailable permissions and unscheduled background work.

## Claim and security rules

- Keep staging/demo separate from real live-school data.
- Production signing keys and credentials stay in restricted stores; candidate-validation secrets are transient and never become production credentials.
- Protect school/role authorization and audit integrity; certify real persisted transactions, not merely mocked interfaces.
- Maintain the payment-processing disabled/fail-closed restriction until separately approved.
- No additional Azure recurring services or charges without authorization.
- GitHub CI execution does not imply Azure deployment or production runtime readiness.

## Completion ledger

| Deliverable | Acceptance proof | State |
| --- | --- | --- |
| Deployment workflow correction (#316) | merged exact-head, protected checks | Pending |
| Six-role crawler (#318) | merged exact-head, protected checks | Pending |
| Azure backend | immutable image, API /health and /version identity | Unverified |
| Azure frontend | deployed build.json identity, browser entry | Unverified |
| Heritage journeys | six authenticated roles, route/browser and persistence evidence | Unverified |
| Operational recovery | isolated restore and rollback evidence | Unverified |
| Sales readiness | working verified link and approved presenter packet | Pending |

Update this ledger only with corresponding evidence. This document itself does not grant Azure access, perform background execution, or certify production.
