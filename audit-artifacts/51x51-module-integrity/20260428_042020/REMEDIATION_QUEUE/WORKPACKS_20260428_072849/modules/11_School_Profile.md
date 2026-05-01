# CROWN Module Remediation - School Profile

Generated: 2026-04-28T07:28:50.3822556-04:00

## Module

- ModuleId: 11
- Layer: SIS Core
- Owner: Dev 2
- P1 FAIL rows: 7
- P2 REVIEW rows: 21

## Required Work

| Priority | Category | Check | Required Fix | Evidence |
|---|---|---|---|---|
| P1 | Tenant-Isolation | Tenant Isolation Tested | Add cross-school denial tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_23_Tenant_Isolation_Tested.txt |
| P1 | Test-Coverage | Unit Tests Exist | Add unit tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_40_Unit_Tests_Exist.txt |
| P1 | Test-Coverage | API Tests Exist | Add API tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_41_API_Tests_Exist.txt |
| P1 | Test-Coverage | Frontend Tests Exist | Add component tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_42_Frontend_Tests_Exist.txt |
| P1 | Test-Coverage | Playwright/E2E Exists | Add Playwright smoke test. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_43_Playwright_E2E_Exists.txt |
| P1 | Test-Coverage | Negative Tests Exist | Add negative coverage. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_44_Negative_Tests_Exist.txt |
| P1 | Product-Governance | Definition of Done Met | Close all missing evidence rows before claiming complete. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_51_Definition_of_Done_Met.txt |
| P2 | Product-Governance | Canonical Definition Exists | Create/approve module canon with scope, exclusions, owner, and acceptance. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_01_Canonical_Definition_Exists.txt |
| P2 | Data-Model | No Shadow Record Risk | Replace duplicate record ownership with Core references. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_12_No_Shadow_Record_Risk.txt |
| P2 | Test-Coverage | Seed/Demo Data Exists | Add deterministic seed fixtures for sandbox testing. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_15_Seed_Demo_Data_Exists.txt |
| P2 | Test-Coverage | Validation Exists | Add validation and negative tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_19_Validation_Exists.txt |
| P2 | Product-Governance | Layer Classification Correct | Fix taxonomy; move misplaced capabilities into correct layer. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_02_Layer_Classification_Correct.txt |
| P2 | Test-Coverage | Authentication Required | Enforce auth on APIs and routes. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_21_Authentication_Required.txt |
| P2 | Permission-Security | Permission Enforcement Exists | Add RBAC checks and tests. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_22_Permission_Enforcement_Exists.txt |
| P2 | Test-Coverage | Audit Logging Exists | Add audit events for mutations/access. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_24_Audit_Logging_Exists.txt |
| P2 | Data-Model | Sensitive Data Handling Defined | Add data classification and access rules. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_25_Sensitive_Data_Handling_Defined.txt |
| P2 | Product-Governance | Owner Assigned | Assign owner and add to module inventory. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_03_Owner_Assigned.txt |
| P2 | General-Remediation | Microsoft/M365/Teams Posture Exists | Add enabled/deferred M365/Teams posture. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_38_Microsoft_M365_Teams_Posture_Exists.txt |
| P2 | Backend-API | External Webhook/API Contract Exists | Add signed webhook/API contract. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_39_External_Webhook_API_Contract_Exists.txt |
| P2 | Frontend-Operations | Essential Functions Defined | Write required functions and acceptance rules. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_04_Essential_Functions_Defined.txt |
| P2 | Test-Coverage | Health/Integrity Check Exists | Add module to integrity gate. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_45_Health_Integrity_Check_Exists.txt |
| P2 | Product-Governance | Production Readiness Notes Exist | Add production readiness note. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_48_Production_Readiness_Notes_Exist.txt |
| P2 | Product-Governance | Support/Triage Path Exists | Add owner/support escalation path. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_49_Support_Triage_Path_Exists.txt |
| P2 | Product-Governance | Out-of-Scope Boundaries Defined | Add exclusion rules to prevent module sprawl. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_05_Out-of-Scope_Boundaries_Defined.txt |
| P2 | Data-Model | No Placeholder/Fake Production Data | Replace placeholders or clearly sandbox-scope them. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_50_No_Placeholder_Fake_Production_Data.txt |
| P2 | Permission-Security | Primary Workflows Designed | Map role workflows and state transitions. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_06_Primary_Workflows_Designed.txt |
| P2 | CI-Gate-Wiring | Lifecycle States Defined | Implement explicit status model and transition validation. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_07_Lifecycle_States_Defined.txt |
| P2 | Permission-Security | Role Responsibilities Defined | Define role-action matrix. | audit-artifacts\51x51-module-integrity\20260428_042020\evidence\11_School_Profile_08_Role_Responsibilities_Defined.txt |

## Completion Standard

This module is not complete until this workpack has zero open rows and the 51x51 audit rerun returns zero FAIL and zero REVIEW for ModuleId 11.
