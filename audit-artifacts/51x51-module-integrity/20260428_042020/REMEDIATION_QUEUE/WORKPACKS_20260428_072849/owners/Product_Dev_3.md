# CROWN 51x51 Remediation Workpack - Product + Dev 3

Generated: 2026-04-28T07:28:50.1481938-04:00

## Decision

**FIX REQUIRED**

## Counts

- Modules affected: 4
- P1 FAIL rows: 29
- P2 REVIEW rows: 46
- Total open rows: 75

## Execution Rule

Do not mark any module complete until every P1 and P2 row is closed, tests are added, CI is wired, and the 51x51 audit reruns with zero FAIL and zero REVIEW for that module.

## P1 FAIL Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 40 | Service & Outreach | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_23_Tenant_Isolation_Tested.txt |
| 40 | Service & Outreach | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_40_Unit_Tests_Exist.txt |
| 40 | Service & Outreach | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_41_API_Tests_Exist.txt |
| 40 | Service & Outreach | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_42_Frontend_Tests_Exist.txt |
| 40 | Service & Outreach | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_43_Playwright_E2E_Exists.txt |
| 40 | Service & Outreach | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_44_Negative_Tests_Exist.txt |
| 40 | Service & Outreach | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_51_Definition_of_Done_Met.txt |
| 44 | Chaplain / Pastoral Care | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_23_Tenant_Isolation_Tested.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_40_Unit_Tests_Exist.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_41_API_Tests_Exist.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_42_Frontend_Tests_Exist.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_43_Playwright_E2E_Exists.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_44_Negative_Tests_Exist.txt |
| 44 | Chaplain / Pastoral Care | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_51_Definition_of_Done_Met.txt |
| 45 | Portrait of the Graduate | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_23_Tenant_Isolation_Tested.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_40_Unit_Tests_Exist.txt |
| 45 | Portrait of the Graduate | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_41_API_Tests_Exist.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_42_Frontend_Tests_Exist.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_43_Playwright_E2E_Exists.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_44_Negative_Tests_Exist.txt |
| 45 | Portrait of the Graduate | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_51_Definition_of_Done_Met.txt |
| 47 | CRM / Marketing Suite | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_23_Tenant_Isolation_Tested.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_40_Unit_Tests_Exist.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_41_API_Tests_Exist.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_42_Frontend_Tests_Exist.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_43_Playwright_E2E_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_44_Negative_Tests_Exist.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | CI Gate Includes Module | Add module test to CI workflow. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_46_CI_Gate_Includes_Module.txt |
| 47 | CRM / Marketing Suite | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_51_Definition_of_Done_Met.txt |

## P2 REVIEW Rows

| ModuleId | Module | Category | Check | Required Fix | Evidence |
|---:|---|---|---|---|---|
| 40 | Service & Outreach | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_19_Validation_Exists.txt |
| 40 | Service & Outreach | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_21_Authentication_Required.txt |
| 40 | Service & Outreach | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_22_Permission_Enforcement_Exists.txt |
| 40 | Service & Outreach | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_24_Audit_Logging_Exists.txt |
| 40 | Service & Outreach | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\40_Service_Outreach_45_Health_Integrity_Check_Exists.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_19_Validation_Exists.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_21_Authentication_Required.txt |
| 44 | Chaplain / Pastoral Care | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_22_Permission_Enforcement_Exists.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_24_Audit_Logging_Exists.txt |
| 44 | Chaplain / Pastoral Care | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\44_Chaplain_Pastoral_Care_45_Health_Integrity_Check_Exists.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_19_Validation_Exists.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_21_Authentication_Required.txt |
| 45 | Portrait of the Graduate | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_22_Permission_Enforcement_Exists.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_24_Audit_Logging_Exists.txt |
| 45 | Portrait of the Graduate | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\45_Portrait_of_the_Graduate_45_Health_Integrity_Check_Exists.txt |
| 47 | CRM / Marketing Suite | Permission-Security | User Operation Exists | Add role-facing screen and action flow. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_10_User_Operation_Exists.txt |
| 47 | CRM / Marketing Suite | Data-Model | Canonical Data Model Exists | Create model/schema or approved contract. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_11_Canonical_Data_Model_Exists.txt |
| 47 | CRM / Marketing Suite | Data-Model | No Shadow Record Risk | Replace duplicate record ownership with Core references. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_12_No_Shadow_Record_Risk.txt |
| 47 | CRM / Marketing Suite | Tenant-Isolation | Tenant Key Present | Add school/tenant FK and scoped access pattern. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_13_Tenant_Key_Present.txt |
| 47 | CRM / Marketing Suite | Data-Model | Migration Exists | Generate and commit migrations. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_14_Migration_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Seed/Demo Data Exists | Add deterministic seed fixtures for sandbox testing. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_15_Seed_Demo_Data_Exists.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | API Endpoint Exists | Create API route/service. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_16_API_Endpoint_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Serializer/Schema Exists | Add serializers/schemas and validation tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_17_Serializer_Schema_Exists.txt |
| 47 | CRM / Marketing Suite | CI-Gate-Wiring | Service Layer Exists | Move workflow logic into service layer. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_18_Service_Layer_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_19_Validation_Exists.txt |
| 47 | CRM / Marketing Suite | Backend-API | Error Handling Exists | Add safe errors and logging. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_20_Error_Handling_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_21_Authentication_Required.txt |
| 47 | CRM / Marketing Suite | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_22_Permission_Enforcement_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_24_Audit_Logging_Exists.txt |
| 47 | CRM / Marketing Suite | Data-Model | Sensitive Data Handling Defined | Add data classification and access rules. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_25_Sensitive_Data_Handling_Defined.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | Route Exists | Add route and navigation entry. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_26_Route_Exists.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | Dashboard/Entry Card Exists | Add dashboard card and module entry. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_27_Dashboard_Entry_Card_Exists.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | Form UI Exists | Add standardized form UI. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_28_Form_UI_Exists.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | Table/List UI Exists | Add list/table UI. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_29_Table_List_UI_Exists.txt |
| 47 | CRM / Marketing Suite | Frontend-Operations | Empty/Loading/Error States Exist | Add complete UI states. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_30_Empty_Loading_Error_States_Exist.txt |
| 47 | CRM / Marketing Suite | Backend-API | KPI Data Source Exists | Wire KPI to backend query or service. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_32_KPI_Data_Source_Exists.txt |
| 47 | CRM / Marketing Suite | Permission-Security | Reporting/Export Exists | Add report/export path with RBAC and audit. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_34_Reporting_Export_Exists.txt |
| 47 | CRM / Marketing Suite | Product-Governance | Core Wiring Exists | Wire to Core canonical records. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_35_Core_Wiring_Exists.txt |
| 47 | CRM / Marketing Suite | General-Remediation | Notification Wiring Exists | Add notification hooks. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_36_Notification_Wiring_Exists.txt |
| 47 | CRM / Marketing Suite | General-Remediation | Calendar Wiring Exists | Add calendar/event integration or mark not applicable. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_37_Calendar_Wiring_Exists.txt |
| 47 | CRM / Marketing Suite | General-Remediation | Microsoft/M365/Teams Posture Exists | Add enabled/deferred M365/Teams posture. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_38_Microsoft_M365_Teams_Posture_Exists.txt |
| 47 | CRM / Marketing Suite | Backend-API | External Webhook/API Contract Exists | Add signed webhook/API contract. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_39_External_Webhook_API_Contract_Exists.txt |
| 47 | CRM / Marketing Suite | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_45_Health_Integrity_Check_Exists.txt |
| 47 | CRM / Marketing Suite | Data-Model | No Placeholder/Fake Production Data | Replace placeholders or clearly sandbox-scope them. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_50_No_Placeholder_Fake_Production_Data.txt |
| 47 | CRM / Marketing Suite | CI-Gate-Wiring | Lifecycle States Defined | Implement explicit status model and transition validation. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_07_Lifecycle_States_Defined.txt |
| 47 | CRM / Marketing Suite | CI-Gate-Wiring | Admin Operation Exists | Add admin screen/API workflow. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\47_CRM_Marketing_Suite_09_Admin_Operation_Exists.txt |

## Verification Required

After repairs, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\execution\136_crown_51x51_module_integrity_audit.ps1 -RunBackendChecks -RunFrontendChecks -RunPlaywright
```
