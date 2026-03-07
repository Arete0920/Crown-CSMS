# Blackbaud to Crown Migration Playbook

## Overview
This playbook covers migration from Blackbaud Education Management (SKY)
into Crown.

---

## Pre-Migration Checklist
- [ ] Crown school record created and configured
- [ ] Blackbaud admin access with data export permissions
- [ ] Designated Crown admin user provisioned
- [ ] Test import completed in sandbox

---

## Required Exports from Blackbaud

| Export | Format | Notes |
|---|---|---|
| Students | CSV (Core Data List) | Include all active |
| Parents / Guardians | CSV | From Relationship Manager |
| Tuition & Billing | CSV | From Tuition Management |
| Financial Aid | CSV | From Award records |
| Payment History | CSV | Last 3 years |

---

## Crown Import Targets

| Blackbaud Data | Crown Model | App |
|---|---|---|
| Students | `Student` | `students` |
| Parents | `Guardian` (via Household) | `households` |
| Tuition & Billing | (configure in Finance Setup) | `finance_setup` |
| Financial Aid | `Award` | `financial_aid` |
| Payment History | `Payment` | `ledger` |

---

## Import Process

1. Export Core Student Data from Blackbaud Lists
2. Map Blackbaud fields to Crown CSV headers:
   - `sys_user_id` → `student_external_id`
   - `first_name` → `student_first_name`
   - `last_name` → `student_last_name`
   - `grad_year` → derive `grade_level`
3. Upload via Crown Import Wizard
4. Validate, Preview, Commit, Verify

---

## Validation Steps

- [ ] Student count matches Blackbaud active roster
- [ ] Guardian emails unique and complete
- [ ] Payment totals reconcile vs. Blackbaud ledger reports
- [ ] Grade levels mapped correctly from graduation year
- [ ] Financial aid award amounts match Blackbaud award records

---

## Common Issues

| Error | Fix |
|---|---|
| Graduation year not mapped to grade_level | Use lookup table (Class of 2027 = Grade 12) |
| Duplicate guardian records | Blackbaud allows duplicate contacts — de-dupe by email |
| Missing household linkage | Ensure family_id field is populated in export |

---

## Notes
Blackbaud exports vary by configuration. Always preview with 5-10 rows before
full commit. Reconcile tuition plan assignments manually in Crown Finance Setup
after student import completes.
