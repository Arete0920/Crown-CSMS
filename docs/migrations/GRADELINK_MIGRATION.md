# Gradelink to Crown Migration Playbook

## Overview
This playbook covers migration from Gradelink SIS into Crown.
Gradelink exports are typically simpler (smaller datasets) — most migrations
complete in a single day.

---

## Pre-Migration Checklist
- [ ] Crown school record created
- [ ] Gradelink admin export access confirmed
- [ ] Test import completed in sandbox

---

## Required Exports from Gradelink

| Export | Format | Location in Gradelink |
|---|---|---|
| Student List | CSV | Reports → Students |
| Parent/Guardian List | CSV | Reports → Parents |
| Grade History | CSV | Reports → Academic |
| Payment History | CSV | Billing → Reports |

---

## Crown Import Targets

| Gradelink Data | Crown Model | App |
|---|---|---|
| Students | `Student` | `students` |
| Parents | `Guardian` (via Household) | `households` |
| Grade History | (manual entry or future Academics import) | `academics` |
| Payment History | `Payment` | `ledger` |

---

## Field Mapping

| Gradelink Field | Crown CSV Header |
|---|---|
| `StudentID` | `student_external_id` |
| `FirstName` | `student_first_name` |
| `LastName` | `student_last_name` |
| `BirthDate` | `student_dob` (YYYY-MM-DD) |
| `Grade` | `grade_level` |
| `Status` | `student_status` |
| `ParentID` | `guardian_external_id` |
| `ParentEmail` | `guardian_email` |
| `Relationship` | `guardian_relationship` |
| `FamilyID` | `household_external_id` |

---

## Validation Steps

- [ ] Student count matches Gradelink active roster
- [ ] Grade level values are valid Crown grade slugs
- [ ] Date of birth format is YYYY-MM-DD
- [ ] Guardian emails populated for all primary contacts
- [ ] Payment totals reconcile vs. Gradelink billing reports

---

## Post-Migration
- Verify enrollment status for each student
- Configure tuition plans in Crown Finance Setup
- Import historical grade records into Crown Academics (if needed)
- Run Crown activation gate before enabling live billing
