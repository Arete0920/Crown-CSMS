# CROWN Final Sprint Execution Packet

Status: execution control under #1374  
Date: 2026-07-18  
Release posture: CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED

## Four-lane operating model

At most four lanes may be active at one time.

1. Release-critical implementation: the only lane permitted to change production-critical code, tenant enforcement, identity behavior, deployment controls, schema controls, or required CI decisions.
2. CI proof and diagnostics: workflow inventory, duplicate-command analysis, failure localization, artifact quality, proof ownership, and staged low-risk improvements.
3. Authenticated runtime evidence: immutable frontend/backend identity, persona routes, tenant propagation, provenance, screenshots, accessibility, console, and network evidence.
4. Recovery and transferability evidence: rollback, restore, RTO/RPO, clean-room setup, bounded-change rehearsal, and documentation-gap discovery.

## Concurrency boundaries

- Only one release-critical implementation pull request may be active.
- The other three lanes must remain documentation, evidence, testing, or read-only analysis unless the implementation lane is closed.
- No lane may change the release identity during an authenticated runtime campaign.
- No required check may be removed, renamed, or weakened without branch-protection inventory and equivalence evidence.
- Documentation may record current evidence but may not convert missing runtime or external evidence into PASS.

## Current lane assignments

### Lane 1: tenant-boundary convergence

Active implementation: #1416 under #1352.

Closure requires exact-head focused tests, broad tests, tenant isolation, permission checks, no unresolved review threads, and linked evidence. This lane does not close the remaining middleware, exemption, audit, background-task, or runtime-proof requirements by itself.

### Lane 2: CI proof hierarchy

Controlled by #1394.

Current work includes command-level overlap inventory, required-check ownership, artifact retention, failure localization, and one-cluster-at-a-time consolidation. The pytest diagnostic split is the first completed localization improvement. No workflow retirement is authorized by this packet.

### Lane 3: authenticated runtime evidence

Controlled by #1274, #1287, #1276, and #1351.

The campaign must bind one unchanged frontend identity and one unchanged backend identity, then capture authenticated school-administrator, teacher, and parent route evidence. Every observed data source must be classified as live, fallback, sample, stub, partial-live, or no-proof.

### Lane 4: recovery and successor operation

Controlled by #1270 and #1393.

The current repository proves a recovery decision workflow and disposable database recovery behavior. Remaining work includes a controlled application rollback, isolated restore exercise or approved equivalent, measured RTO/RPO, and clean-room operation by a qualified successor using repository-controlled instructions only.

## Ordered completion path

1. Diagnose and settle the exact-head broad-suite result for #1416.
2. Merge #1416 only after all required exact-head checks pass.
3. Complete the remaining tenant consumer, exemption, audit, task-binding, and middleware-equivalence work.
4. Freeze one deployed frontend/backend identity and execute the authenticated runtime campaign.
5. Complete canonical household, guardian, and student identity reconciliation.
6. Execute rollback and restore exercises and record observed RTO/RPO.
7. Complete external secret-store and payment-scope evidence.
8. Complete the CI ownership and duplicate-workflow ledger.
9. Run the clean-room successor exercise.
10. Reconcile release documentation to the final main SHA and run one final same-SHA authority ceremony.

## Merge discipline

Every implementation merge requires:

- exact head SHA recorded;
- intended changed-file scope verified;
- focused validation passed;
- applicable broad validation passed;
- required checks complete and successful;
- no unresolved review threads;
- evidence linked to the controlling issue;
- Founder/Product Owner disposition recorded through the solo-developer workaround where independent approval is unavailable.

## Non-claims

This packet does not authorize production, certify a deployed runtime, prove rollback or restore, approve payment processing, close any release blocker, or replace the final same-SHA production-readiness ceremony.
