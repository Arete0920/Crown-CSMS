# Campaign 3 Verified Findings Ledger

**Campaign:** Data model, migration, and relational integrity  
**Pinned repository SHA:** `02f61af9367b5ee17c9da494aec9c268ff33dd6a`  
**Campaign PR:** #1547  
**Controlling issue:** #1527  
**Production decision:** PRODUCTION NOT APPROVED

## Decision rules

- Findings below are source-verified against the pinned SHA.
- A source-level integrity gap is not represented as proof of corrupt production data.
- Every P1/P2 finding requires bounded remediation, reproducible evidence, exact-head CI, and rollback or forward-fix planning where schema or persisted data is involved.
- No destructive migration, table collapse, or compatibility retirement is authorized.

## C3-P1-001 — Compatibility household tenant relationships are not database-enforced

**Severity:** P1  
**Confidence:** High  
**Remediation issue:** #1548

`households.Household`, `households.Guardian`, and `households.Student` persist bare UUID `school_id` columns. Guardian and Student also reference Household, but the model contains no visible database invariant requiring the child `school_id` to equal the referenced household's `school_id`. The tenant identifier is not a foreign key to `core.School`.

Request scoping validates the selected school and filters querysets by `school_id`, but that read boundary does not prove that direct ORM writes, scripts, seeds, migrations, admin operations, or historical rows preserve parent-child tenant equality.

Required evidence:

- complete writer inventory;
- orphan and cross-tenant mismatch queries by tenant;
- representative reconciliation totals;
- non-destructive enforcement design;
- migration timing, lock impact, rollback, and forward-fix proof.

## C3-P1-002 — Operational academics uses a second student and enrollment authority

**Severity:** P1  
**Confidence:** High  
**Remediation issue:** #1549

The accepted architecture declares `core.Family`, `core.Guardian`, and `core.Student` the canonical operational write authority. However:

- `academics.models` imports `Student` from `households.models`;
- `academics.Enrollment.student` points to `households.Student`;
- academics parent access resolves `households.Guardian` and `households.Student`;
- the academics seed writes compatibility households, guardians, students, and enrollments;
- `core.models` separately defines `core.Enrollment` pointing to `core.Student`.

This creates two active operational student/enrollment spines with non-equivalent fields and relationships. Source evidence does not prove row corruption, but it does prove unresolved authority, mapping, and lifecycle ambiguity across academics, gradebook, parent access, and reporting.

Required evidence:

- classify every academics and gradebook reader/writer;
- freeze row counts and tenant distribution for both spines;
- define deterministic student and enrollment mapping;
- rehearse non-destructive expand-contract migration;
- prove parent, teacher, gradebook, reporting, and transcript equivalence;
- prove rollback or forward-fix without losing new canonical writes.

## C3-P1-003 — Academics relationships duplicate tenant ownership without cross-model invariants

**Severity:** P1  
**Confidence:** High  
**Remediation issue:** #1550

Multiple academics records carry a bare `school_id` while also referencing tenant-owned parents. Examples include:

- Term -> AcademicYear;
- Section -> Course and Term;
- Enrollment -> Section and Student;
- TeacherAssignment -> Section and Staff;
- AssignmentCategory and Assignment -> Section;
- Submission -> Assignment and Enrollment;
- downstream curriculum and grade relationships.

The visible uniqueness constraints generally protect entity combinations, not equality between each record's `school_id` and the tenant of all referenced parents. This leaves direct ORM, seed, migration, task, or admin paths capable of constructing internally inconsistent cross-tenant graphs unless every writer separately enforces the invariant.

Required evidence:

- relationship-by-relationship tenant invariant matrix;
- all writer and bulk-update paths;
- reproducible mismatch audit queries;
- model/service/database enforcement strategy;
- negative tests for direct ORM and API/service writes;
- zero-unexplained rehearsal results and rollback proof.

## Verified consumer starting set

The source review identified active compatibility-domain consumers including:

- `backend/academics/models.py`;
- `backend/academics/views.py`;
- `backend/scripts/seed_academics_readonly.py`;
- `backend/guardian_household_wizard/views.py`;
- `backend/core/scoping.py`;
- `backend/core/management/commands/seed_demo.py`;
- `backend/onboarding/views.py`;
- `backend/applications/views_admissions.py`;
- `backend/parent360/api/views.py`;
- household, academics, parent360, admissions, and tenant-isolation tests.

This is a starting set, not a complete dependency graph.

## Campaign status

Campaign 3 remains open. The three P1 findings above require remediation or explicit Founder/Product Owner disposition. This ledger does not authorize production, destructive migration, or compatibility-domain retirement.
