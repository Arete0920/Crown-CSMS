# Student Identity Bridge Contract

## Status

Repair Unit 1 establishes an explicit crosswalk between canonical `core.Student` and compatibility `households.Student`. It does **not** migrate downstream consumers, change roster foreign keys, or infer historical identity equivalence.

## Authority

- `core.Student` remains the canonical operational student identity.
- `households.Student` remains a compatibility identity used by existing roster, portal, gradebook, billing, OneRoster, reenrollment, and related consumers until separately migrated and verified.
- `StudentIdentityLink` is the only approved student-level bridge introduced by this repair unit.

## Required invariants

Every link must:

1. belong to exactly one `core.School`;
2. reference exactly one canonical `core.Student`;
3. reference exactly one compatibility `households.Student`;
4. use one-to-one uniqueness on both student sides;
5. reject any cross-school relationship;
6. carry an explicit mapping source;
7. require an evidence reference before a mapping can be marked `verified`.

Both student references use `PROTECT` so identity evidence cannot be silently removed by cascaded deletion.

## Prohibited matching

No automatic mapping may be created from:

- UUID coincidence;
- first/last name;
- email;
- grade;
- household position;
- family membership alone;
- date ordering;
- fabricated or substituted date of birth;
- any composite heuristic without explicit provenance establishing identity equivalence.

The reconciliation command therefore performs counts only. Candidate inference is intentionally disabled because the current two student models do not share a deterministic, trustworthy identity key.

## Reconciliation evidence

`python manage.py reconcile_student_identities` is read-only. Per school it reports canonical totals, compatibility totals, mapped and verified totals, pending mappings, unmatched records, and invalid cross-tenant links. It performs no writes and no candidate matching.

A compatibility retirement decision requires production-shaped, tenant-by-tenant reconciliation with unexplained identity records reduced to zero or explicitly dispositioned.

## Repair-unit boundary

This repair unit intentionally excludes:

- admissions/application writer cutover;
- Student360 resolver changes;
- Attendance membership changes;
- `academics.Enrollment.student` migration;
- Gradebook, Billing, OneRoster, reenrollment, or portal cutovers;
- automatic data backfills.

Those changes must use the bridge in separately bounded repair units with their own exact-head proof.
