# CROWN Module Remediation - Notifications Framework

Generated: 2026-04-28T07:28:50.3542655-04:00

## Module

- ModuleId: 5
- Layer: Platform Core
- Owner: Dev 1
- P1 FAIL rows: 7
- P2 REVIEW rows: 5

## Required Work

| Priority | Category | Check | Required Fix | Evidence |
|---|---|---|---|---|
| P1 | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_23_Tenant_Isolation_Tested.txt |
| P1 | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_40_Unit_Tests_Exist.txt |
| P1 | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_41_API_Tests_Exist.txt |
| P1 | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_42_Frontend_Tests_Exist.txt |
| P1 | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_43_Playwright_E2E_Exists.txt |
| P1 | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_44_Negative_Tests_Exist.txt |
| P1 | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_51_Definition_of_Done_Met.txt |
| P2 | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_19_Validation_Exists.txt |
| P2 | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_21_Authentication_Required.txt |
| P2 | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_22_Permission_Enforcement_Exists.txt |
| P2 | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_24_Audit_Logging_Exists.txt |
| P2 | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\05_Notifications_Framework_45_Health_Integrity_Check_Exists.txt |

## Completion Standard

This module is not complete until this workpack has zero open rows and the 51x51 audit rerun returns zero FAIL and zero REVIEW for ModuleId 5.
