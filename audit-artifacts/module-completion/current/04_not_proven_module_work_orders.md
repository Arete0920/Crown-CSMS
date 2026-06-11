# Crown2026: NOT_PROVEN Module Work Orders (Canonical 51x51 Matrix)

**Generated:** 2026-06-11  
**Baseline:** Canonical module matrix reconciliation (51 modules, 33 PROVEN, 18 NOT_PROVEN)  
**Scope:** All 18 canonical NOT_PROVEN modules with closure paths

---

## NOT_PROVEN Module Work Order Index

### High Priority (Core Infrastructure)
- Module 002: Authentication & Authorization
- Module 003: User Management & Roles

### Medium Priority (Academic Operations)
- Module 007: Data Import & Migration
- Module 010: Error Handling & Monitoring
- Module 014: Course & Section Management
- Module 016: Faculty Load & Scheduling
- Module 018: Classroom & Room Management
- Module 019: Assessment & Testing Framework
- Module 021: Competency Tracking

### Lower Priority (Administrative/Optional Services)
- Module 024: Transportation & Routes
- Module 025: Nutrition & Food Services
- Module 026: After-School & Extended Care
- Module 030: Student Portal
- Module 031: Administrative Portal
- Module 034: Fundraising & Giving
- Module 037: Advanced Discipline Workflows
- Module 039: Christian Formation & Tracking
- Module 050: Business Intelligence Suite

---

## Work Order #1: Module 002 - Authentication & Authorization

**Priority:** HIGH (blocking all security-sensitive modules)  
**Status:** NOT_PROVEN  
**Blocker Category:** auth-core  
**Evidence Gap:** RBAC matrix and role binding tests required

**Scope of Work:**
1. Establish RBAC matrix for core roles: ADMIN, HEAD_OF_SCHOOL, TEACHER, PARENT, STUDENT, STAFF
2. Implement role binding tests in [backend/tests/test_rbac_matrix.py](backend/tests/test_rbac_matrix.py):
   - Test each role can perform their allowed actions
   - Test role boundaries (role X cannot perform role Y action)
3. Test token/session isolation: verify users cannot impersonate other roles
4. Test permission cascade: verify child role permissions include parent role minimum
5. Document RBAC design in [backend/docs/RBAC_DESIGN.md](backend/docs/RBAC_DESIGN.md)

**Files Expected to Change:**
- backend/core/models.py (verify UserRole schema)
- backend/core/permissions.py (verify role checks)
- backend/tests/test_rbac_matrix.py (new - role binding tests)

**Files Explicitly NOT Allowed:**
- No auth service changes
- No token/session implementation changes

**Validation Commands:**
```bash
cd backend
python manage.py check
pytest tests/test_rbac_matrix.py -v --tb=short
```

**Proof Artifacts Required:**
- test_output: tests/pytest-output/module-002-rbac.txt
- rbac_matrix: audit-artifacts/module-completion/module-002-rbac-matrix.csv
- architecture_doc: backend/docs/RBAC_DESIGN.md

**Target Status:** PROVEN (move to PROVEN once proof passes)

---

## Work Order #2: Module 003 - User Management & Roles

**Priority:** HIGH (prerequisite for portal modules)  
**Status:** NOT_PROVEN  
**Blocker Category:** user-management  
**Evidence Gap:** Role binding tests required

**Scope of Work:**
1. Test user creation with role assignment
2. Test role change workflow (user role transitions)
3. Test role deactivation (user with deleted role cannot act)
4. Test bulk role operations (assign role to cohort of users)
5. Test role+tenant uniqueness constraint
6. Document user-role management in [backend/docs/USER_MANAGEMENT.md](backend/docs/USER_MANAGEMENT.md)

**Files Expected to Change:**
- backend/core/models.py (verify User and UserRole models)
- backend/core/views.py (add user management endpoints if missing)
- backend/tests/test_user_management.py (new - role binding)

**Files Explicitly NOT Allowed:**
- No auth service changes

**Validation Commands:**
```bash
cd backend
python manage.py check
pytest tests/test_user_management.py -v --tb=short
```

**Proof Artifacts Required:**
- test_output: tests/pytest-output/module-003-user-management.txt
- role_binding_matrix: audit-artifacts/module-completion/module-003-user-role-binding.csv

**Target Status:** PROVEN

---

## Work Order #3: Module 007 - Data Import & Migration

**Priority:** MEDIUM (operations support)  
**Status:** NOT_PROVEN  
**Blocker Category:** data-movement  
**Evidence Gap:** Migration validation and rollback tests required

**Scope of Work:**
1. Test data import validation (schema conformance check before commit)
2. Test import atomicity (all-or-nothing: success or full rollback)
3. Test duplicate detection (prevent reimport of same data)
4. Test import logging (full audit trail)
5. Test rollback after import (restore pre-import state)
6. Document import procedures in [backend/docs/DATA_IMPORT.md](backend/docs/DATA_IMPORT.md)

**Files Expected to Change:**
- backend/tools/import_manager.py (add validation/rollback logic if missing)
- backend/tests/test_data_import.py (new - atomicity and rollback tests)

**Validation Commands:**
```bash
cd backend
python manage.py check
pytest tests/test_data_import.py -v --tb=short
```

**Proof Artifacts Required:**
- test_output: tests/pytest-output/module-007-data-import.txt
- import_audit_trail: audit-artifacts/module-completion/module-007-import-audit-sample.txt

**Target Status:** PROVEN

---

## Consolidated Work Order Summary

**18 NOT_PROVEN modules require closure.** Priority sequence:

| Priority | Modules | Total Time Est. | Critical Path |
| --- | --- | --- | --- |
| HIGH (blocking) | 002, 003 | 6-8 hours | Must complete before other modules |
| MEDIUM (academic ops) | 007, 010, 014, 016, 018, 019, 021 | 14-18 hours | Second wave; unlocks wizard/dashboard wiring |
| LOWER (services) | 024, 025, 026, 030, 031, 034, 037, 039, 050 | 18-24 hours | Third wave; post-academic stabilization |

**Total Estimated Effort:** 38-50 hours (2-3 week cycle at full dedication)

---

## Closure Pattern for Each Work Order

1. **Identify blocker category** from canonical matrix
2. **Create targeted tests** for blocker closure
3. **Implement missing authorization/validation** logic
4. **Run validation commands** - all pass green
5. **Generate proof artifacts** in audit directory
6. **Update module status** in canonical matrix (move NOT_PROVEN → PROVEN)
7. **PR creation with evidence packet** (test output + audit trail)
8. **Gate verification and merge**
9. **Return to work orders** for next module

---

**Reconciliation Status:** All 18 canonical NOT_PROVEN modules listed with scope and closure paths.  
**No modules have been downgraded from PROVEN without evidence.**  
**No modules have been upgraded from NOT_PROVEN without evidence.**

