# CROWN 51x51 Remediation Workpack - Dev 3

Generated: 2026-04-28T07:28:50.1209612-04:00

## Decision

**FIX REQUIRED**

## Counts

- Modules affected: 5
- P1 FAIL rows: 35
- P2 REVIEW rows: 25
- Total open rows: 60

## Execution Rule

Do not mark any module complete until every P1 and P2 row is closed, tests are added, CI is wired, and the 51x51 audit reruns with zero FAIL and zero REVIEW for that module.

## P1 FAIL Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 27 | Communications | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_23_Tenant_Isolation_Tested.txt |
| 27 | Communications | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_40_Unit_Tests_Exist.txt |
| 27 | Communications | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_41_API_Tests_Exist.txt |
| 27 | Communications | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_42_Frontend_Tests_Exist.txt |
| 27 | Communications | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_43_Playwright_E2E_Exists.txt |
| 27 | Communications | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_44_Negative_Tests_Exist.txt |
| 27 | Communications | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_51_Definition_of_Done_Met.txt |
| 33 | Nurse Office / Health Office | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_23_Tenant_Isolation_Tested.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_40_Unit_Tests_Exist.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_41_API_Tests_Exist.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_42_Frontend_Tests_Exist.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_43_Playwright_E2E_Exists.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_44_Negative_Tests_Exist.txt |
| 33 | Nurse Office / Health Office | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_51_Definition_of_Done_Met.txt |
| 34 | Transportation | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_23_Tenant_Isolation_Tested.txt |
| 34 | Transportation | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_40_Unit_Tests_Exist.txt |
| 34 | Transportation | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_41_API_Tests_Exist.txt |
| 34 | Transportation | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_42_Frontend_Tests_Exist.txt |
| 34 | Transportation | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_43_Playwright_E2E_Exists.txt |
| 34 | Transportation | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_44_Negative_Tests_Exist.txt |
| 34 | Transportation | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_51_Definition_of_Done_Met.txt |
| 36 | Volunteer / Family Engagement | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_23_Tenant_Isolation_Tested.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_40_Unit_Tests_Exist.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_41_API_Tests_Exist.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_42_Frontend_Tests_Exist.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_43_Playwright_E2E_Exists.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_44_Negative_Tests_Exist.txt |
| 36 | Volunteer / Family Engagement | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_51_Definition_of_Done_Met.txt |
| 38 | Extended Discipline Workflows | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_23_Tenant_Isolation_Tested.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_40_Unit_Tests_Exist.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_41_API_Tests_Exist.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_42_Frontend_Tests_Exist.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_43_Playwright_E2E_Exists.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_44_Negative_Tests_Exist.txt |
| 38 | Extended Discipline Workflows | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_51_Definition_of_Done_Met.txt |

## P2 REVIEW Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 27 | Communications | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_19_Validation_Exists.txt |
| 27 | Communications | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_21_Authentication_Required.txt |
| 27 | Communications | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_22_Permission_Enforcement_Exists.txt |
| 27 | Communications | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_24_Audit_Logging_Exists.txt |
| 27 | Communications | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\27_Communications_45_Health_Integrity_Check_Exists.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_19_Validation_Exists.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_21_Authentication_Required.txt |
| 33 | Nurse Office / Health Office | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_22_Permission_Enforcement_Exists.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_24_Audit_Logging_Exists.txt |
| 33 | Nurse Office / Health Office | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\33_Nurse_Office_Health_Office_45_Health_Integrity_Check_Exists.txt |
| 34 | Transportation | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_19_Validation_Exists.txt |
| 34 | Transportation | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_21_Authentication_Required.txt |
| 34 | Transportation | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_22_Permission_Enforcement_Exists.txt |
| 34 | Transportation | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_24_Audit_Logging_Exists.txt |
| 34 | Transportation | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\34_Transportation_45_Health_Integrity_Check_Exists.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_19_Validation_Exists.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_21_Authentication_Required.txt |
| 36 | Volunteer / Family Engagement | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_22_Permission_Enforcement_Exists.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_24_Audit_Logging_Exists.txt |
| 36 | Volunteer / Family Engagement | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\36_Volunteer_Family_Engagement_45_Health_Integrity_Check_Exists.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_19_Validation_Exists.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_21_Authentication_Required.txt |
| 38 | Extended Discipline Workflows | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_22_Permission_Enforcement_Exists.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_24_Audit_Logging_Exists.txt |
| 38 | Extended Discipline Workflows | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\38_Extended_Discipline_Workflows_45_Health_Integrity_Check_Exists.txt |

## Verification Required

After repairs, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1 -RunBackendChecks -RunFrontendChecks -RunPlaywright
```
