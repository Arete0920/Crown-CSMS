# Legacy Source-System to CROWN Migration Playbook

## Purpose

This playbook defines the standard process for migrating school data from an existing external school-management, billing, enrollment, or academic system into CROWN.

The source vendor is intentionally not named in repository documentation. Migration logic is based on exported data structure, field meaning, reconciliation requirements, and CROWN's canonical domain model.

## Pre-Migration Checklist

- [ ] CROWN school tenant created and configured
- [ ] Designated school administrator identified
- [ ] Source-system export access confirmed
- [ ] Approved secure data-transfer method confirmed
- [ ] Required datasets inventoried
- [ ] Field-mapping workbook completed
- [ ] Test import completed in a sandbox or controlled rehearsal environment
- [ ] Rollback/recovery approach documented

## Typical Source Exports

Depending on the school and migration scope:

- Students
- Parents / guardians / households
- Staff and users
- Enrollment status/history
- Courses / sections / rosters
- Grade history / transcripts
- Attendance history
- Tuition plans / charges
- Financial-aid awards
- Payment / ledger history
- Communications or operational records when explicitly in scope

## Canonical CROWN Targets

| Source data class | CROWN authority |
|---|---|
| Students | canonical student identity/domain |
| Parents / guardians | household / guardian identity |
| Staff / users | canonical staff/user identity |
| Enrollment | enrollment lifecycle |
| Courses / sections / rosters | academics |
| Grade history | academics / student records |
| Billing / tuition | billing / finance setup |
| Financial aid | financial-aid authority |
| Payment history | ledger/payment history boundary |

## Import Process

1. Export approved source datasets.
2. Preserve the original source package as controlled migration evidence.
3. Map source fields to canonical CROWN fields.
4. Normalize dates, identifiers, statuses, grade levels, and relationship values.
5. Validate required fields and referential relationships.
6. Preview a representative sample.
7. Run a full rehearsal import.
8. Produce a reconciliation report.
9. Resolve material exceptions.
10. Run the controlled production migration.
11. Reconcile production counts, relationships, balances, and representative records.

## Validation

At minimum verify:

- student counts;
- guardian/household relationships;
- unique identity mapping;
- enrollment status;
- grade-level mapping;
- course/section/roster integrity;
- financial totals where applicable;
- financial-aid totals where applicable;
- historical academic data where applicable;
- rejected/exception records;
- cross-tenant isolation.

## Common Issues

- inconsistent date formats;
- duplicate household/contact records;
- missing guardian email/contact information;
- source identifiers reused or absent;
- inconsistent grade labels;
- incomplete household linkage;
- historical records lacking current canonical relationships;
- source financial totals that require explicit reconciliation before import.

Do not silently coerce ambiguous records. Record the exception and obtain disposition.

## Post-Migration

- verify representative student/family/staff records;
- complete tenant configuration;
- configure any school-specific finance or academic setup;
- run role-based validation;
- complete training;
- obtain school administrator acceptance;
- follow the canonical School Implementation Runbook before go-live.

See: `docs/operations/SCHOOL_IMPLEMENTATION_RUNBOOK.md`.
