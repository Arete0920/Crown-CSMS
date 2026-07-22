# Campaign 3 — Data Model, Migration, and Relational Integrity

**Status:** ACTIVE — findings only  
**Pinned main SHA:** `02f61af9367b5ee17c9da494aec9c268ff33dd6a`  
**Controlling issue:** #1527  
**Related release blockers:** #1353, #1352, #1374, #1548, #1549, #1550  
**Production decision:** PRODUCTION NOT APPROVED

## Objective

Establish an evidence-backed integrity assessment of CROWN's persisted data model, migration graph, tenant boundaries, relational constraints, compatibility domains, reconciliation paths, and rollback safety. This campaign does not authorize destructive migration, compatibility-table retirement, production deployment, or release approval.

## Primary audit domains

1. Canonical `core.Family`, `core.Guardian`, and `core.Student` write authority.
2. `households.Household`, `households.Guardian`, and `households.Student` compatibility tables.
3. `crown_api` person, household, membership, and student compatibility domain.
4. Admissions bridges between canonical and compatibility identity families.
5. Guardian-household wizard transaction, idempotency, and rollback behavior.
6. Enrollment, tuition, ledger, billing, attendance, financial-aid, portal, reporting, import, export, task, signal, and seed consumers.
7. Tenant ownership represented by real foreign keys versus bare UUID fields.
8. Cross-table uniqueness, nullability, orphan risk, duplicate risk, and delete behavior.
9. Migration ordering, merge migrations, historical model safety, data backfills, reversibility, lock exposure, and exact-SHA deployment controls.
10. Expand-contract convergence, reconciliation counts, rollback checkpoints, and safe legacy-retirement criteria.

## Evidence already confirmed

- `core.Family`, `core.Guardian`, and `core.Student` are the accepted canonical operational write records.
- `households` persists separate household, guardian, and student tables with UUID primary keys and bare indexed `school_id` UUID fields.
- `crown_api` persists a separate normalized person/household/membership/student family.
- Admissions contains explicit compatibility bridges and therefore prevents retirement by model-name similarity.
- The guardian-household wizard writes transactionally to the canonical core spine and must not write to legacy domains.
- Active academics models and access paths still depend on `households.Student` and `households.Guardian`, while `core.Enrollment` separately depends on `core.Student`.
- Complete compatibility convergence remains open under #1353.

## Initial integrity hypotheses requiring proof

### H1 — Bare tenant identifiers permit relational drift

Persisted records with bare UUID `school_id` columns rather than database foreign keys to `core.School` may retain orphan tenant identifiers or bypass application-level ownership controls. The campaign must enumerate every such model and prove tenant validity for every reader and writer.

### H2 — Parent/child tenant consistency is not database enforced

The campaign must enumerate every relationship in which a child row stores a tenant identifier while also referencing a tenant-owned parent. This includes, but is not limited to, household/guardian/student, admissions application/applicant/household, academics term/year, section/course/term, enrollment/section/student, teacher assignment/section/staff, assignment/category/section, submission/assignment/enrollment, billing, attendance, financial aid, portal, and reporting relationships.

For every pair, the campaign must record:

- child model and tenant field;
- parent model and tenant ownership path;
- database constraint or absence of one;
- every writer and bulk-update path;
- a reproducible mismatch/orphan query;
- current mismatch count by tenant;
- remediation or formal disposition.

A household-only query is not sufficient.

### H3 — Canonical and compatibility identities lack a complete deterministic mapping

The accepted architecture records write authority but not full cross-family equivalence. The campaign must enumerate identifiers and semantics, define deterministic mapping rules, and quantify unmatched, duplicate, ambiguous, orphan, null/invalid, and cross-tenant records by tenant before any convergence work.

### H4 — Migration safety is incompletely proven

Repository migrations and historical evidence must be checked for irreversible operations, unsafe `RunPython` behavior, table/column renames by inference, long-lock operations, non-atomic assumptions, deployment-time migration coupling, and rollback gaps.

Migration-lock proof must use PostgreSQL and the controlled `migrate_with_lock` path on the exact candidate SHA. The rehearsal must launch a competing migration runner while the first holds the advisory lock and prove that the competitor times out or is rejected. SQLite, direct `manage.py migrate`, or a single-runner rehearsal cannot satisfy the lock-safety requirement.

### H5 — Consumer inventory is incomplete

The current identity inventory explicitly describes itself as a starting set. Every reader, writer, task, signal, serializer, report, import/export path, fixture, seed, test, frontend contract, management command, and administrative mutation path must be classified before compatibility retirement can be planned.

## Required evidence ledger

For each finding record:

- severity: P0, P1, P2, P3, or INFO;
- confidence;
- exact SHA, file, model, field, migration, symbol, or query;
- affected tenants and business processes;
- reproduction or database query;
- current controls and bypass paths;
- remediation boundary;
- required tests and migration rehearsal;
- rollback or forward-fix strategy;
- linked issue and PR.

## Required verification

- Django system and migration checks on the pinned SHA;
- complete migration graph and leaf-node inspection;
- model-to-table inventory with constraints and indexes;
- consumer search for all canonical and compatibility models;
- complete tenant-relationship matrix with mismatch and orphan queries for every parent/child pair;
- per-tenant reconciliation metrics for pre-count, post-count, mapped, unmatched, duplicate candidate, orphan, null/invalid, rejected cross-tenant, manual disposition, and unexplained count;
- production-shaped PostgreSQL migration rehearsal using `migrate_with_lock` at the exact SHA;
- competing-runner advisory-lock proof showing timeout or rejection;
- measured migration duration and lock behavior;
- rollback/forward-fix rehearsal;
- exact-head CI and independent review for each remediation PR.

## Exit criteria

Campaign 3 cannot close until:

1. every persisted identity family and active consumer is classified;
2. every tenant-bearing parent/child relationship is enumerated and tested;
3. relational and tenant-integrity gaps are fixed or formally dispositioned;
4. migration graph and deployment sequence are proven on an immutable SHA;
5. PostgreSQL advisory-lock contention is proven with competing runners through `migrate_with_lock`;
6. reconciliation queries produce reproducible per-tenant metrics for every required anomaly category;
7. every nonzero unmatched, duplicate, orphan, null/invalid, ambiguous, or cross-tenant anomaly is remediated or formally dispositioned;
8. the remaining unexplained count is zero for every tenant and entity;
9. deterministic cross-family mapping is documented;
10. expand-contract and rollback checkpoints are approved;
11. all P0/P1/P2 remediation issues are closed or formally accepted by the Founder/Product Owner;
12. residual risk is linked to #1374.

No result from this campaign alone authorizes production.
