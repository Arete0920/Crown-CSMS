# FACTS to Crown Migration Playbook

## Overview
This playbook guides the migration of student, financial, and enrollment data
from FACTS School Management into Crown.

---

## Pre-Migration Checklist
- [ ] Crown school record created and configured
- [ ] Onboarding tasks seeded (`python manage.py seed_onboarding_tasks <school_id>`)
- [ ] FACTS admin access confirmed — export permissions granted
- [ ] Designated Crown admin user provisioned
- [ ] Test import completed in sandbox environment

---

## Required Exports from FACTS

| Export | Format | Notes |
|---|---|---|
| Students | CSV | Include all active + pending |
| Parents / Guardians | CSV | Link via guardian_external_id |
| Tuition Plans | CSV | Per-family, per-year |
| Financial Aid Records | CSV | Include award amount + type |
| Ledger History (Payments) | CSV | Last 3 years minimum |

---

## Crown Import Targets

| FACTS Data | Crown Model | App |
|---|---|---|
| Students | `Student` | `students` |
| Parents | `Guardian` (via Household) | `households` |
| Tuition Plans | (configure manually in Finance Setup) | `finance_setup` |
| Financial Aid | `Award` | `financial_aid` |
| Payments | `Payment` (read-only import, no mutation) | `ledger` |

---

## Import Process

1. Upload Students CSV via Import Wizard (`POST /api/v1/onboarding/imports/`)
2. Validate — fix any header/encoding errors
3. Preview first 20 rows — confirm household groupings
4. Commit — Crown creates Students + Households
5. Verify — confirm counts match FACTS export row count

---

## Validation Steps

- [ ] Total student count matches FACTS export count
- [ ] Guardian email addresses are unique (de-duped)
- [ ] Ledger payment totals reconcile within $0.00 variance
- [ ] Enrollment status matches (active vs. pending)
- [ ] Financial aid award totals match FACTS reports

---

## Common Issues

| Error | Fix |
|---|---|
| `student_dob` format invalid | Ensure YYYY-MM-DD format |
| Duplicate `household_external_id` | Review FACTS household groupings |
| Missing `guardian_email` | Required field — obtain from school |

---

## Post-Migration
- Complete remaining onboarding tasks (Tuition Plans, FA, Teacher Invites)
- Run activation gate check: `GET /api/v1/onboarding/<school_id>/can-activate/`
- Enable live billing only after gate returns `can_activate: true`
