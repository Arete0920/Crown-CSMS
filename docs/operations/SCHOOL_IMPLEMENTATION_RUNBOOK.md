# CROWN School Implementation Runbook

**Purpose:** Define one repeatable implementation path from signed agreement to stable live operation.
**Audience:** owner, implementation lead, technical operator, client success, school administrator
**Applies to:** early-adopter and standard school implementations

## Operating principle

A school is not "implemented" because a contract is signed or data is imported. Implementation is complete only when the school can perform its agreed daily workflows, users are trained, data is reconciled, support ownership is clear, and the school has completed an initial live-operation review.

## Stage 1 — Contract and implementation intake

Required inputs:

- signed agreement and approved commercial terms;
- school legal/name identity and primary contacts;
- current SIS/provider and known contract end date;
- selected CROWN modules and launch scope;
- target launch date;
- approximate enrollment and grade configuration;
- data sources and export availability;
- identity/authentication requirements;
- payment processing status, if applicable;
- implementation owner on both sides.

Exit criteria:

- scope is explicit;
- launch date is feasible;
- unsupported integrations are identified;
- no payment capability is implied unless separately authorized.

## Stage 2 — Discovery and data mapping

Inventory:

- students;
- households/guardians;
- staff/users;
- academic year/terms;
- grade levels;
- courses/sections/rosters;
- admissions/enrollment records;
- attendance;
- gradebook/transcript data where in scope;
- billing/financial-aid records where in scope;
- communications and operational modules selected for launch.

For each source dataset record:

- source system;
- export format;
- authoritative field;
- CROWN destination;
- transformation rule;
- owner;
- validation method;
- exception handling.

Exit criteria:

- one mapping authority exists;
- duplicate or conflicting source truth is dispositioned before migration;
- sensitive data transfer method is approved.

## Stage 3 — Tenant provisioning and configuration

Create and verify:

- school tenant;
- academic calendar;
- school year/terms;
- grade structure;
- roles and permissions;
- administrator accounts;
- school-level configuration;
- module entitlements;
- notification defaults;
- required integrations that are authorized and available.

Security proof:

- school isolation;
- role boundaries;
- administrator access;
- no cross-school visibility;
- synthetic/sandbox verification before production data load.

## Stage 4 — Migration rehearsal

Perform a rehearsal using the approved mapping.

Required checks:

- record counts;
- required-field completeness;
- duplicate detection;
- household/student relationships;
- staff/user identity alignment;
- course/section/roster integrity;
- financial totals where applicable;
- historical data boundaries;
- rejected/exception records.

Produce a reconciliation report.

Do not proceed to production migration with unexplained material variances.

## Stage 5 — Production migration

Requirements:

- approved source extract;
- immutable migration package/hash where practical;
- controlled migration window;
- backup/rollback plan;
- migration operator identified;
- school contact available;
- post-migration reconciliation.

Exit criteria:

- agreed counts reconcile;
- critical relationships validate;
- school administrator confirms representative records;
- no unresolved high-severity migration defect remains.

## Stage 6 — Role-based validation

Validate representative workflows for:

### Administrator
- users/roles;
- student records;
- enrollment;
- reporting;
- operational dashboards.

### Teacher
- roster;
- attendance;
- gradebook;
- communications;
- assigned operational workflows.

### Parent/guardian
- student access;
- communications;
- billing/financial information where enabled;
- forms/workflows in launch scope.

### Student
- schedule;
- assignments/grades where enabled;
- school resources in scope.

All testing must occur in the correct school context.

## Stage 7 — Training

Default delivery is digital:

- implementation orientation;
- role-based video/user guides;
- live Zoom training;
- administrator office hours;
- launch checklist.

On-site training is optional and separately scheduled.

Training completion must identify:

- school administrator;
- backup administrator;
- support escalation contact;
- internal school communication plan.

## Stage 8 — Go-live authorization

Go-live requires:

- migration reconciliation accepted;
- role validation completed;
- critical security/release gates green for the deployed version;
- support ownership confirmed;
- known limitations disclosed;
- rollback/recovery path identified;
- school administrator approval.

No informal "soft launch" overrides unresolved critical security, tenant, migration, or authorization defects.

## Stage 9 — Hypercare

Review at approximately:

- Day 1
- Day 7
- Day 30
- Day 60
- Day 90

Track:

- login/adoption;
- support volume;
- failed workflows;
- unresolved data issues;
- payment volume where authorized;
- module usage;
- satisfaction;
- renewal/referral signals.

## Stage 10 — Stable operation

A school exits implementation when:

- agreed launch workflows are in routine use;
- critical support issues are closed;
- ownership has transferred from implementation to client success/operations;
- documentation reflects any school-specific configuration;
- no tenant-specific source-code fork exists.

## Early-adopter cohort

For the initial 40-school cohort, capture comparable implementation metrics:

- days from contract to tenant ready;
- days to first clean migration;
- training hours;
- support tickets in first 30 days;
- active family adoption;
- active staff adoption;
- module usage;
- 30/60/90-day satisfaction;
- renewal intent;
- referrals.

These metrics are product-market-fit and implementation evidence, not merely sales statistics.

## Key-person risk control

At least one person other than the founder should eventually be able to execute this runbook using documented credentials, procedures, and approved access.

The handoff standard is successful execution, not document possession.
