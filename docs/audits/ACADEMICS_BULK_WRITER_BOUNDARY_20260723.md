# Academics bulk and database-writer boundary

Date: 2026-07-23
Controlling issue: #1570

This tranche was reconstructed directly from the merged `main` authority after #1579, so its review diff contains only the bulk-writer scope documented below.

## Scope proven by the application guard

The application process installs one QuerySet interception layer for these tenant-bearing academics models:

- `Term`
- `Section`
- `Enrollment`
- `TeacherAssignment`
- `AssignmentCategory`
- `Assignment`
- `Submission`

Within a configured Django process, the guard:

1. rejects authority reassignment through `QuerySet.update()`;
2. permits only a narrow lifecycle exception: clearing a nullable authority relation to `NULL`, including Django deletion-collector cleanup;
3. validates every `bulk_create()` object through the registered pre-save authority guards before persistence;
4. resolves the write database through an explicit `.using()` alias or the database router;
5. locks every persisted target row and validates projected authority before an authority-changing `bulk_update()`;
6. permits the validated internal update issued by Django's `bulk_update()` implementation without opening a general QuerySet bypass;
7. permits non-authority queryset and bulk updates;
8. performs validation and persistence in the same write-database transaction.

The nullable-clear exception removes an authority reference; it does not permit assigning a different school, course, term, teacher, student, section, category, assignment, enrollment, or staff authority through `QuerySet.update()`.

The regression suite proves valid same-school operations, cross-school rejection before persistence, unchanged rows after rejected batches, safe non-authority updates, nullable-authority clearing and deletion-collector compatibility, and Submission lineage validation. It does not claim a simulated database failure after a partial write.

## Writer inventory observations

Repository search identified normal ORM writers in academics APIs, gradebook services, seed commands, integration code, and section-assignment/staffing workflows. These paths use model saves, manager creates, `update_or_create()`, or QuerySet operations and therefore execute through the application controls when the configured Django application is loaded.

The similarly named `section_scheduler_wizard.models.Section` is a separate model from `academics.models.Section`; it must not be counted as proof for or against the academics relational guard.

The inventory also identified `academics_ro.management.commands.seed_academics_ro_demo`, which previously issued raw `INSERT` and `DELETE` statements against the shared `course` and `section` tables. This tranche replaces those statements with routed, transaction-bound `academics.models.Course` and `academics.models.Section` ORM operations so the command executes through the same tenant-integrity controls.

No other intentional in-repository raw-SQL writer targeting the governed academics tables was identified by the indexed searches performed for this tranche. That search result does not prove that an external administrator or database client cannot issue SQL.

## Explicit database boundary

Django signals and QuerySet wrappers cannot intercept:

- direct SQL issued through an external database client;
- a privileged administrator modifying rows outside the application process;
- disabled or bypassed application startup hooks;
- future migration `RunSQL` operations unless independently reviewed.

Accordingly, this tranche does **not** claim schema-level or administrator-proof enforcement.

The production control boundary is:

1. the runtime application credential must not be shared for interactive administration;
2. direct write-capable database credentials must be restricted to controlled migration and emergency procedures;
3. migrations and operational scripts touching governed tables require tenant-integrity review and evidence;
4. direct SQL changes require an audit record, before/after invariant query, and rollback or forward-fix plan;
5. a future database-trigger or composite-key design may strengthen enforcement, but requires production-shaped rehearsal before adoption.

## Closure statement

This evidence supports closure of the Django queryset and bulk-operation bypass class plus remediation of the identified in-repository raw-SQL seed writer. It does not authorize production, certify external database writers, or close canonical Student/Enrollment convergence under #1549.
