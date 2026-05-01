# CROWN 51x51 Remediation Workpack - Dev 4

Generated: 2026-04-28T07:28:50.1311971-04:00

## Decision

**FIX REQUIRED**

## Counts

- Modules affected: 3
- P1 FAIL rows: 21
- P2 REVIEW rows: 15
- Total open rows: 36

## Execution Rule

Do not mark any module complete until every P1 and P2 row is closed, tests are added, CI is wired, and the 51x51 audit reruns with zero FAIL and zero REVIEW for that module.

## P1 FAIL Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 28 | Parent Portal | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_23_Tenant_Isolation_Tested.txt |
| 28 | Parent Portal | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_40_Unit_Tests_Exist.txt |
| 28 | Parent Portal | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_41_API_Tests_Exist.txt |
| 28 | Parent Portal | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_42_Frontend_Tests_Exist.txt |
| 28 | Parent Portal | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_43_Playwright_E2E_Exists.txt |
| 28 | Parent Portal | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_44_Negative_Tests_Exist.txt |
| 28 | Parent Portal | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_51_Definition_of_Done_Met.txt |
| 8 | Shared Frontend Shell | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_23_Tenant_Isolation_Tested.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_40_Unit_Tests_Exist.txt |
| 8 | Shared Frontend Shell | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_41_API_Tests_Exist.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_42_Frontend_Tests_Exist.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_43_Playwright_E2E_Exists.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_44_Negative_Tests_Exist.txt |
| 8 | Shared Frontend Shell | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_51_Definition_of_Done_Met.txt |
| 9 | Shared Design System | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_23_Tenant_Isolation_Tested.txt |
| 9 | Shared Design System | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_40_Unit_Tests_Exist.txt |
| 9 | Shared Design System | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_41_API_Tests_Exist.txt |
| 9 | Shared Design System | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_42_Frontend_Tests_Exist.txt |
| 9 | Shared Design System | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_43_Playwright_E2E_Exists.txt |
| 9 | Shared Design System | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_44_Negative_Tests_Exist.txt |
| 9 | Shared Design System | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_51_Definition_of_Done_Met.txt |

## P2 REVIEW Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 28 | Parent Portal | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_19_Validation_Exists.txt |
| 28 | Parent Portal | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_21_Authentication_Required.txt |
| 28 | Parent Portal | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_22_Permission_Enforcement_Exists.txt |
| 28 | Parent Portal | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_24_Audit_Logging_Exists.txt |
| 28 | Parent Portal | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\28_Parent_Portal_45_Health_Integrity_Check_Exists.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_19_Validation_Exists.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_21_Authentication_Required.txt |
| 8 | Shared Frontend Shell | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_22_Permission_Enforcement_Exists.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_24_Audit_Logging_Exists.txt |
| 8 | Shared Frontend Shell | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\08_Shared_Frontend_Shell_45_Health_Integrity_Check_Exists.txt |
| 9 | Shared Design System | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_19_Validation_Exists.txt |
| 9 | Shared Design System | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_21_Authentication_Required.txt |
| 9 | Shared Design System | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_22_Permission_Enforcement_Exists.txt |
| 9 | Shared Design System | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_24_Audit_Logging_Exists.txt |
| 9 | Shared Design System | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\09_Shared_Design_System_45_Health_Integrity_Check_Exists.txt |

## Verification Required

After repairs, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1 -RunBackendChecks -RunFrontendChecks -RunPlaywright
```
