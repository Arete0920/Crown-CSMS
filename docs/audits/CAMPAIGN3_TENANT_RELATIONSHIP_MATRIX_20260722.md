# Campaign 3 Tenant Relationship Matrix

**Status:** ACTIVE — source inventory, not data certification  
**Pinned source SHA:** `02f61af9367b5ee17c9da494aec9c268ff33dd6a`  
**Controlling issues:** #1527, #1548, #1549, #1550  
**Production decision:** PRODUCTION NOT APPROVED

## Purpose

Enumerate persisted child/parent relationships where the child stores its own tenant identifier while also referencing one or more tenant-owned parent rows. These relationships require proof that all tenant identifiers agree, every writer fails closed, and existing data has zero unexplained mismatches.

This document is a verified seed inventory and closure contract. The hand-maintained table is not, by itself, evidence that the active model universe is complete or that production data is clean. Closure requires a generated inventory of every installed, non-abstract persisted model at the exact candidate SHA and a machine-reconciled comparison showing that every tenant-bearing relationship is represented or formally classified.

## Verified relationship groups at the pinned source

| Domain | Child | Child tenant field | Parent relationship | Parent tenant path | Visible equality constraint | Required mismatch proof |
|---|---|---|---|---|---|---|
| Households | `households.Guardian` | `school_id` | `household` | `household.school_id` | None identified | child school differs from household school; invalid school identifier |
| Households | `households.Student` | `school_id` | `household` | `household.school_id` | None identified | child school differs from household school; invalid school identifier |
| Admissions | `applications.Application` | `school_id` | `household` | `household.school_id` | None identified | application school differs from household school |
| Admissions | `applications.Applicant` | `school_id` | `application` | `application.school_id` | None identified | applicant school differs from application school |
| Admissions | `applications.Applicant` | `school_id` | optional `student` | `student.school_id` | None identified | linked student differs from applicant/application school |
| Admissions | `applications.ApplicationEvent` | `school_id` | `application` | `application.school_id` | None identified | event school differs from application school |
| Admissions | `applications.ApplicationChecklistItem` | `school_id` | `application` | `application.school_id` | None identified | checklist school differs from application school |
| Admissions | `applications.ApplicationChecklistDocument` | `school_id` | `checklist_item` | `checklist_item.school_id` | None identified | document school differs from checklist/application school |
| Admissions | `applications.EnrollmentContract` | `school_id` | `application` | `application.school_id` | None identified | contract school differs from application school |
| Admissions | `applications.EnrollmentContract` | `school_id` | optional `amended_from` | `amended_from.school_id` | None identified | amendment crosses tenant boundary |
| Academics | `academics.Term` | `school_id` | `academic_year` | `academic_year.school_id` | None identified | term school differs from academic year school |
| Academics | `academics.Section` | `school_id` | `course` | `course.school_id` | None identified | section school differs from course school |
| Academics | `academics.Section` | `school_id` | optional `term_ref` | `term_ref.school_id` | None identified | section school differs from term school |
| Academics | `academics.Enrollment` | `school_id` | `section` | `section.school_id` | None identified | enrollment school differs from section school |
| Academics | `academics.Enrollment` | `school_id` | `student` | compatibility `student.school_id` | None identified | enrollment school differs from student school |
| Academics | `academics.TeacherAssignment` | `school_id` | `section` | `section.school_id` | None identified | assignment school differs from section school |
| Academics | `academics.TeacherAssignment` | `school_id` | `staff` | `staff.school_id` | None identified | assignment school differs from staff school |
| Gradebook | `academics.AssignmentCategory` | `school_id` | `section` | `section.school_id` | None identified | category school differs from section school |
| Gradebook | `academics.Assignment` | `school_id` | `section` | `section.school_id` | None identified | assignment school differs from section school |
| Gradebook | `academics.Assignment` | `school_id` | `category` | `category.school_id` | None identified | assignment school differs from category school |
| Gradebook | `academics.Assignment` | `school_id` | optional `lesson` | `lesson.school_id` | None identified | assignment school differs from lesson school |
| Gradebook | `academics.Assignment` | `school_id` | optional `objective` | `objective.school_id` | None identified | assignment school differs from objective school |
| Gradebook | `academics.Submission` | `school_id` | `assignment` | `assignment.school_id` | None identified | submission school differs from assignment school |
| Gradebook | `academics.Submission` | `school_id` | `enrollment` | `enrollment.school_id` | None identified | submission school differs from enrollment school |
| Gradebook | `academics.Grade` | `school_id` | `submission` | `submission.school_id` | None identified | grade school differs from submission school |
| Gradebook | `gradebook.GradeEntry` | `school_id` | `section` | `section.school_id` | None identified | grade entry school differs from section school |
| Gradebook | `gradebook.GradeEntry` | `school_id` | `student` | `student.school_id` | None identified | grade entry school differs from student school |
| Gradebook | `gradebook.GradeEntry` | `school_id` | optional `assignment` | `assignment.school_id` | None identified | grade entry school differs from assignment school |
| Curriculum | `academics.Unit` | `school_id` | `course` | `course.school_id` | None identified | unit school differs from course school |
| Curriculum | `academics.Unit` | `school_id` | optional `curriculum_source` | `curriculum_source.school_id` | None identified | unit school differs from curriculum source school |
| Curriculum | `academics.Lesson` | `school_id` | `unit` | `unit.school_id` | None identified | lesson school differs from unit school |
| Curriculum | `academics.PublisherObjective` | `school_id` | `lesson` | `lesson.school_id` | None identified | objective school differs from lesson school |
| Curriculum | `academics.LessonPlan` | `school_id` | `section` | `section.school_id` | None identified | lesson plan school differs from section school |
| Curriculum | `academics.LessonResource` | `school_id` | `lesson` | `lesson.school_id` | None identified | lesson resource school differs from lesson school |
| Mastery | `academics.MasteryRecord` | `school_id` | `student` | `student.school_id` | None identified | mastery record school differs from student school |
| Mastery | `academics.MasteryRecord` | `school_id` | `objective` | `objective.school_id` | None identified | mastery record school differs from objective school |
| Mastery | `academics.MasteryRecord` | `school_id` | optional `evidence_assignment` | `evidence_assignment.school_id` | None identified | mastery evidence crosses tenant boundary |
| Transcript | `academics.TranscriptEntry` | `school_id` | `student` | `student.school_id` | None identified | transcript school differs from student school |
| Transcript | `academics.TranscriptEntry` | `school_id` | `course` | `course.school_id` | None identified | transcript school differs from course school |
| Transcript | `academics.TranscriptEntry` | `school_id` | optional `term` | `term.school_id` | None identified | transcript school differs from term school |
| Home Academy | `home_academy.HomeAcademyEnrollment` | UUID `school_id` | optional `program` | `program.school_id` | None identified | enrollment school differs from program school |
| Home Academy | `home_academy.Offering` | UUID `school_id` | optional `program` | `program.school_id` | None identified | offering school differs from program school |
| Home Academy | `home_academy.OfferingEnrollment` | UUID `school_id` | `offering` | `offering.school_id` | None identified | offering enrollment differs from offering school |
| Home Academy | `home_academy.OfferingEnrollment` | UUID `school_id` | optional `home_academy_enrollment` | `home_academy_enrollment.school_id` | None identified | linked enrollments cross school boundary |

The Home Academy integer tenant identifiers are also a representation-consistency finding because the primary school domain uses UUID identifiers. They require explicit mapping or formal isolation proof; they must not be silently compared or coerced as though they were the same identifier family.

## Complete active-model-universe control

Before any zero-unexplained claim, an exact-SHA crawler must inspect the Django application registry and emit every installed, non-abstract, managed persisted model with:

- application label, model label, database table, and migration ownership;
- every field named or functioning as a tenant identifier, including `school_id`, school foreign keys, organization identifiers, and compatibility aliases;
- every foreign key, one-to-one field, and many-to-many through model;
- the complete parent tenant path for each related model;
- field type compatibility between child and parent tenant identifiers;
- nullability and deletion behavior;
- constraints and indexes that enforce, or fail to enforce, tenant equality;
- classification as tenant-only, one-parent, multiple-parent, compatibility/historical, migration-state-only, archived/non-importable, or formally non-tenant;
- a reason and evidence reference for every model or relationship excluded from mismatch testing.

The generated inventory must be reconciled against the relationship registry. Closure fails if any installed persisted model, tenant field, or tenant-owned relationship is unclassified, if duplicate registry entries obscure coverage, or if a registered path no longer resolves at the exact candidate SHA.

## Additional domains requiring generated enumeration

Repository source indicates tenant persistence in at least:

- billing, ledger, dunning, payments, and financial aid;
- attendance and discipline;
- communications and outbox;
- HR, classroom, and professional development;
- board oversight and governance;
- advancement, subscriptions, analytics, and customer health;
- outreach and safety;
- fee-schedule wizards;
- Crown API audit, user, person, household, membership, and compatibility models.

This list is a search starting point, not a completeness boundary.

## Required crawler output

For every active relationship, produce:

- application, model, table, child tenant field, parent field, and complete parent tenant path;
- database constraints, indexes, nullability, and delete behavior;
- all serializers, views, services, tasks, signals, imports, seeds, admin actions, migrations, and bulk operations that write it;
- per-tenant input row count;
- normal/consistent row count;
- null tenant count and invalid tenant count as separate categories;
- null parent count and dangling/orphan parent count as separate categories;
- parent-child tenant mismatch count;
- duplicate candidate count;
- rejected cross-tenant write count;
- documented manual-disposition count;
- unexplained count.

## Identity-level reconciliation requirement

Aggregate counters are not sufficient evidence of zero unexplained records. For each model and tenant, the audit must emit a reproducible identity-level partition, or an equivalent checksum-backed artifact, in which every input primary key belongs to exactly one outcome:

1. normal and tenant-consistent;
2. invalid or null tenant identifier;
3. null optional parent;
4. dangling/orphan parent;
5. parent-child tenant mismatch;
6. duplicate or ambiguous candidate;
7. rejected cross-tenant write evidence;
8. documented manual disposition with record identifier, reason, approver, and evidence reference.

Required reconciliation equations:

- `input_ids = union(all outcome ID sets)`;
- every outcome ID set is reproducible from saved query logic;
- outcome sets are mutually exclusive unless an overlap ledger explicitly records and explains each overlapping ID;
- `input_count = accounted_unique_id_count`;
- `unexplained_ids = input_ids - accounted_ids`;
- `unexplained_count = 0` for every tenant, model, and relationship before closure.

Inner joins that silently discard null or dangling relationships cannot satisfy this requirement. A manual-disposition aggregate without record identity, reason, and evidence cannot satisfy this requirement.

## Closure rule

No relationship group is closed by source inspection or aggregate counts alone. Closure requires:

- generated exact-SHA proof that the complete active persisted model universe is classified;
- reproducible identity-level or checksum-backed PostgreSQL query artifacts;
- zero unexplained IDs for every tenant, model, and relationship;
- negative writer tests proving cross-tenant operations fail closed;
- migration and lock-impact analysis where enforcement changes schema;
- rollback or forward-fix rehearsal;
- exact-head CI and independent review.

No result from this matrix authorizes production.
