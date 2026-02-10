# Demo Smoke Proof (Feb 16) - Read-Only Endpoint Verification

**Date:** 2026-02-10  
**Time:** 2026-02-10 02:48:39  
**API Base:** ` http://127.0.0.1:8000 `  
**School (X-School-Id):** ` b45b8c5a-6708-4597-aad9-a226627b2962 `  
**Section:** ` 044882e0-3405-4542-a237-32f1adf4f047 `  
**Student (expected row):** ` da6e706b-ea3f-4047-aa0b-0dbcc0e4aac5 `  

---

## Auth
- Token obtained: [OK]

## Tenant scoping
All requests executed with:
- ` Authorization: Bearer <present> ` [OK]
- ` X-School-Id: <present> ` [OK]

---

## Endpoint Checks (Read-Only)

### 1) Academics - Section Roster
- URL: ` http://127.0.0.1:8000/api/v1/academics/sections/044882e0-3405-4542-a237-32f1adf4f047/roster/ `
- Status: [OK] (JSON parsed)
- Shape verified:
  - section_id [OK]
  - section_name [OK]
  - course_code [OK]
  - counts.students [OK]
  - students[] [OK]
- Observed:
  - counts.students = **1**
  - first student: **Brooks, Ava** (` da6e706b-ea3f-4047-aa0b-0dbcc0e4aac5 `)

### 2) Gradebook - Section Grades Grid
- URL: ` http://127.0.0.1:8000/api/v1/gradebook/sections/044882e0-3405-4542-a237-32f1adf4f047/grades/ `
- Status: [OK] (JSON parsed)
- Shape verified:
  - section_id [OK]
  - assignments[] [OK]
  - rows[] [OK]
- Observed:
  - assignments = **5**
  - rows = **1**
  - expected student row present: **YES**

### 3) Gradebook - Section Assignments
- URL: ` http://127.0.0.1:8000/api/v1/gradebook/sections/044882e0-3405-4542-a237-32f1adf4f047/assignments/ `
- Status: [OK] (JSON parsed)
- Shape verified:
  - section_id [OK]
  - assignments[] [OK]
- Observed:
  - assignments count = **5**
  - sample assignment (first): **Final Exam / 100.0**

---

## Outcome
[OK] Smoke proof complete. Endpoints are live, tenant-scoped, and returning canonical shapes.

**Notes**
- If "expected student row present" is NO, seed data may not include grade entries for that student; endpoints and UI remain valid and defensive.
- This smoke test validates the core Feb 16 demo path: Sections -> Roster -> Student -> Gradebook/Assignments.
- All endpoints are read-only and tenant-scoped via X-School-Id header.

