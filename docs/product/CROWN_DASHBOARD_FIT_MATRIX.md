# CROWN Dashboard Fit Matrix

Status: Planning Control Matrix
Parent Canon: `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`
Release Authority: `docs/CURRENT_RELEASE_STATUS.md`

## Purpose

This matrix maps each dashboard to its source module, live data requirement, persona access, freshness requirement, sensitivity level, drilldown contract, and certification state.

Dashboards are fitted after modules. A dashboard cannot certify a module. It can only expose module truth that is already backed by verified service/API/snapshot evidence.

## Dashboard State Vocabulary

| State | Meaning |
|---|---|
| Scaffold | Component/route/template exists, but live module proof is missing. |
| Hybrid | Some live or snapshot-backed behavior exists, but sample/fallback/demo dependency remains. |
| Live | Live service/API or certified snapshot feeds the dashboard, but full certification is not complete. |
| Certified | Live/snapshot data, freshness, permissions, tenant boundaries, tests, runtime proof, and independent review are complete. |

## Dashboard Payload Requirements

Every production-visible dashboard payload must declare:

- `dashboard_key`
- `module_key`
- `schema_version`
- `served_from`: `live`, `snapshot`, `stale_snapshot`, `sample`, `fallback`, `unavailable`, or `error`
- `source_module`
- `generated_at`
- `expires_at`, if snapshot-backed
- `sensitivity_level`
- `metrics`
- `alerts`
- `queue`
- `drilldowns`
- `redactions`, if any

## Global Fit Rules

1. Registry coverage is not dashboard completion.
2. Component rendering is not dashboard completion.
3. Sample/template data is not production proof.
4. Production-visible dashboards require live service/API-backed data or certified snapshot data.
5. Hybrid dashboards must show provenance and cannot be promoted without removing unresolved fallback/sample dependency.
6. Sensitive dashboards require role redaction and small-cell suppression.
7. Dashboard summary and drilldown counts must reconcile or explain why they differ.
8. Dashboard access must be enforced by dashboard key on the backend.
9. Drilldowns must be paginated, tenant-filtered, and permission-filtered.
10. Exports require explicit export permission, redaction, audit, and retention rules.

## Matrix Columns

| Field | Meaning |
|---|---|
| Dashboard Key | Stable dashboard identifier. |
| Dashboard Name | User-facing dashboard name. |
| Source Module | Module that owns the operational truth. |
| Current Cert State | Scaffold/Hybrid/Live/Certified. |
| Primary Personas | Main users. |
| Data Source Required | Live service/API or certified snapshot requirement. |
| Freshness SLA | Maximum acceptable data age. |
| Sensitivity | Public/Internal/Restricted/Confidential/Highly Sensitive. |
| Required Metrics | First-class KPIs. |
| Required Alerts | Actionable warnings. |
| Required Queue | Work items. |
| Drilldown Required | Yes/No/Partial. |
| Export Allowed | Yes/No/Restricted. |
| Blocking Questions | Items blocking certification. |

## Tier 1 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| attendance | Attendance Operations | attendance | Hybrid | attendance_admin, registrar, school_admin, teacher scoped | Live attendance summary service or certified snapshot | Confidential | Verify operational attendance model/API, strict tenant/role checks, correction audit, freshness SLA. |
| billing | Billing | billing-tuition-ledger | Scaffold | finance_admin, school_admin limited | Live billing/ledger summary service | Highly Sensitive | Verify ledger source, payment status, small-cell suppression, export rules. |
| financial-aid | Financial Aid | financial-aid | Scaffold | aid_director, finance_admin limited | Live aid award/application summary service | Highly Sensitive | Verify confidential access, award lifecycle, billing impact. |
| registrar | Registrar | enrollment-registrar | Scaffold | registrar, school_admin | Live enrollment/student-record summary service | Confidential | Verify enrollment state, document workflow, transcript/request queues. |

## Tier 2 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| scheduling | Scheduling | scheduling | Scaffold | registrar, academic_admin, school_admin | Live scheduling/conflict summary service | Restricted | Verify schedule model, conflict detection, publish state. |
| gradebook | Gradebook | gradebook | Scaffold | teacher scoped, academic_admin, school_admin | Live gradebook summary service | Confidential | Verify teacher scope, missing work, finalization status. |
| student-care | Student Care | student-care-discipline | Scaffold | student_care, school_admin restricted | Live student-care summary service with redaction | Highly Sensitive | Define restricted notes, small-cell suppression, audit. |
| activities-athletics | Activities / Athletics | activities-athletics | Scaffold | athletics_director, student_life, school_admin | Live activities/athletics roster/event summary service | Confidential | Verify eligibility source and parent/student visibility. |
| communications | Communications | communications | Scaffold | communications_director, school_admin, teacher scoped | Live message/delivery summary service | Confidential | Verify role targeting, emergency messages, delivery status. |

## Tier 3 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| school-administrator | School Administrator | administrator-portal | Scaffold | school_admin, head_of_school | Aggregated certified module summaries | Restricted | Define executive rollup, redaction, and drilldown permissions. |
| school-board | School Board | board-governance | Scaffold | board_member, school_admin restricted | Certified board/governance summary service | Highly Sensitive | Define board data boundaries and export rules. |
| master-control | Master Control | platform/control layer | Scaffold | master_control, super_admin | Platform control summary service | Highly Sensitive | Define tenant switching, access, and audit. |
| admissions | Admissions | admissions | Scaffold | admissions_manager, school_admin | Live admissions pipeline service | Confidential | Verify pipeline stages and enrollment conversion. |
| advancement | Advancement | advancement-operations | Scaffold | advancement_officer, school_admin restricted | Live advancement summary service | Highly Sensitive | Define donor privacy and finance boundary. |

## Tier 4 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| hr | HR | hr | Scaffold | hr_manager, school_admin restricted | Live HR compliance/lifecycle summary service | Highly Sensitive | Define staff sensitive data boundaries. |
| facilities | Facilities | facilities | Scaffold | facilities_manager, school_admin | Live work-order/location summary service | Internal | Verify work order model and location ownership. |
| health-office | Health Office | health-office | Scaffold | nurse, health_office, school_admin restricted | Live health summary with strict redaction | Highly Sensitive | Define health privacy, audit, and stale data behavior. |
| transportation | Transportation | transportation | Scaffold | transportation_manager, school_admin | Live route/rider summary service | Confidential | Verify family address source and rider scope. |
| food-service | Food Service | food-service | Scaffold | food_service_manager, finance_admin limited | Live meal/account summary service | Confidential | Define billing boundary and account privacy. |
| it-support | IT Support | it-support | Scaffold | it_support, master_control, school_admin limited | Live ticket/access summary service | Restricted | Define access/security ticket visibility. |

## Tier 5 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| fine-arts | Fine Arts | fine-arts | Scaffold | fine_arts_director, school_admin | Live participation/event summary service | Confidential | Verify roster/event source. |
| athletics-director | Athletics Director | activities-athletics | Scaffold | athletics_director, school_admin | Live athletics-specific summary service | Confidential | Verify split from general activities dashboard. |
| library-media | Library / Media | library-media | Scaffold | librarian, media_specialist, school_admin | Live circulation/resource summary service | Confidential | Define borrowing privacy. |
| extended-care | Extended Care | extended-care | Scaffold | extended_care_manager, school_admin, finance limited | Live care session summary service | Confidential | Verify check-in/out, custody, and billing link. |
| summer-camp | Summer Camp | summer-camp | Scaffold | summer_camp_coordinator, extended_care_manager | Live camp roster/session summary service | Confidential | Verify API route and seasonal data source. |
| safety-security | Safety / Security | safety-security | Scaffold | safety_manager, security_officer, school_admin restricted | Live incident/drill/security summary service | Highly Sensitive | Define incident redaction and audit. |
| curriculum-pd | Curriculum / PD | curriculum-pd | Scaffold | curriculum_director, pd_coordinator, school_admin | Live curriculum/PD summary service | Restricted | Verify curriculum versioning and PD approvals. |

## Tier 6 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| chaplain-spiritual-life | Chaplain / Spiritual Life | spiritual-life | Scaffold | chaplain, spiritual_life, school_admin restricted | Live mission/spiritual-life summary with redaction | Highly Sensitive | Define pastoral confidentiality boundaries. |
| advancement-operations | Advancement Operations | advancement-operations | Scaffold | advancement_officer, school_admin restricted | Live advancement ops summary service | Highly Sensitive | Define donor privacy and gift boundary. |
| volunteer-management | Volunteer Management | volunteer-management | Scaffold | volunteer_coordinator, school_admin | Live volunteer approval/opportunity summary service | Highly Sensitive | Define background check visibility. |
| portrait-service | Portrait / Service | service-outreach-portrait | Scaffold | service_learning_coordinator, school_admin | Live service/portrait summary service | Confidential | Define graduation linkage and approval workflow. |
| alumni-relations | Alumni Relations | alumni-relations | Scaffold | alumni_relations, advancement_officer | Live alumni engagement summary service | Confidential | Define alumni conversion and contact permissions. |
| network-benchmarking | Network Benchmarking | network-benchmarking | Scaffold | platform_leadership, master_control | Certified anonymized aggregate service | Highly Sensitive | Must prove anonymization and small-cell suppression. |

## Tier 7 Dashboards

| Dashboard Key | Dashboard Name | Source Module | Current Cert State | Primary Personas | Data Source Required | Sensitivity | Blocking Questions |
|---|---|---|---|---|---|---|---|
| implementation-success | Implementation Success | implementation-success | Scaffold | implementation_team, master_control | Live onboarding/customer readiness service | Restricted | Define customer readiness source. |
| data-migration | Data Migration | data-migration | Scaffold | data_ops, master_control | Live import job/validation summary service | Highly Sensitive | Define rollback/backfill evidence. |
| integrations-automation | Integrations / Automation | integrations-automation | Scaffold | integrations_team, it_team, master_control | Live integration job/sync summary service | Highly Sensitive | Define retry, dedupe, and secret redaction. |
| compliance-audit | Compliance Audit | compliance-audit | Scaffold | compliance_team, master_control | Live compliance evidence/exception summary service | Restricted | Define evidence retention and exception workflow. |
| revenue-operations | Revenue Operations | revenue-operations | Scaffold | revenue_ops, master_control | Live internal revenue ops summary service | Restricted | Ensure customer/school data separation. |
| release-reliability | Release Reliability | release-reliability | Hybrid | release_team, platform_certification | Current-head release evidence service or certified snapshot | Internal | Remove sample fallback and enforce current evidence. |
| dashboard-certification-center | Dashboard Certification Center | dashboard-certification | Live | platform_certification, compliance, release_team | Runtime-derived registry/certification service | Internal | Verify no template contamination and evidence linkage. |

## Standard Dashboard Metrics Pattern

Every dashboard should define:

- 4-8 primary KPIs
- alert set
- work queue
- recent activity
- drilldown targets
- freshness display
- provenance display
- role-specific actions
- export rules

## Certification Blockers

A dashboard row blocks certification if any of these are unresolved:

- source module not certified or live enough to feed dashboard
- data source is sample/template/fallback without sandbox-only exception
- payload lacks provenance
- freshness SLA missing
- role-specific redaction missing
- small-cell suppression missing where needed
- drilldown contract missing
- export policy missing
- backend dashboard-key permission missing
- tenant proof missing
- screenshot/Playwright/runtime proof missing
- independent review missing
