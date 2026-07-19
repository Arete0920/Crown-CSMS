# CROWN Final Sprint Execution Packet

Status: execution control under #1374  
Observed main SHA: `12f2af47abdebcf459f8d009d04538cc031348d7`  
Release posture: production not approved

## Four active lanes

1. Release-critical implementation: one production-critical code or workflow lane at a time.
2. Architecture, documentation, and CI proof: inventories, authority records, duplicate-execution analysis, and evidence quality.
3. Authenticated runtime evidence: exact deployed identity, persona routes, school context, screenshots, network, console, accessibility, and provenance.
4. Recovery and successor operation: rollback, restore, measured RTO/RPO, and clean-room transferability.

## Current authority

- PR #1419 merged and preserved production fail-closed tenant behavior while supporting narrow forced-auth fixtures.
- PR #1420 merged at `12f2af47abdebcf459f8d009d04538cc031348d7`.
- PR #1420 corrected live-runtime artifact promotion and passed broad Tests plus the sandbox evidence workflow.
- No authenticated deployed-runtime campaign has yet been accepted for the resulting main SHA.
- Production remains NO-GO.

## Lane priorities

### Lane 1 — release-critical implementation

Do not begin a second production-critical change until the post-#1420 deployment/runtime disposition is known. The next bounded tenant work is structured audit evidence and remaining consumer convergence under #1352.

### Lane 2 — architecture and CI proof

- maintain the tenant inventory and retirement ledger;
- inventory workflow purpose, trigger, path filters, jobs, commands, artifacts, timeouts, proof owner, and required-check role;
- separate merge, release, runtime, scheduled, advisory, and obsolete proof;
- remove no control before equivalence and rollback evidence.

### Lane 3 — authenticated runtime evidence

For one unchanged deployed frontend/backend identity, capture:

- school administrator: `/school-admin-dashboard`, `/admin`, `/dash/admin`;
- teacher: `/teacher`, `/dash/teacher`;
- parent: `/parent`, `/dash/parent`;
- final URL, screenshot, auth state, school context, console counts, failed network counts, observed APIs, provenance, and disposition.

### Lane 4 — recovery and successor operation

Verified source correction:

- rollback handling is tied to the actual deployment step;
- the prior forced secondary failure is removed.

Still required:

- controlled application rollback drill;
- isolated restore exercise or approved equivalent;
- measured RTO/RPO and decision tree;
- clean-room clone, configure, test, modify, deploy, operate, roll back, and recover exercise by a qualified successor.

## Ordered completion

1. Observe post-#1420 deployment and runtime evidence.
2. Inspect exact deployed SHA and artifacts.
3. Repair only from concrete failure evidence or record the passing result.
4. Complete tenant audit and consumer convergence.
5. Complete canonical household, guardian, and student identity work.
6. Execute rollback and restore exercises.
7. Complete external-secret and payment-scope evidence.
8. Complete CI proof hierarchy.
9. Complete clean-room successor operation.
10. Reconcile final release documents and run one final same-SHA authority ceremony.

## Merge discipline

Every merge requires exact head and base, intended file scope, focused and broad validation, terminal required checks, no unresolved review threads, linked evidence, solo-owner disposition where needed, and no unsupported production claim.

## Scope boundary

This packet does not certify deployment, recovery, transferability, payment processing, blocker closure, or production authorization.