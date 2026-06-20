# Dashboard Certification Truth

Generated: 2026-06-20T05:07:42.594161

## Counts

| registry_count | matrix_count | state_register_count | factory_count | certified_count | certifiable_now_count | missing_review_only_count | missing_proof_count | missing_implementation_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | 42 | 40 | 0 | 0 | 0 | 0 | 40 | 0 |

## Denominator Reconciliation

```json
{
  "recommended_canonical_count": 40,
  "registry_keys_not_in_matrix": [
    "student-care"
  ],
  "matrix_keys_not_in_registry": [
    "parent",
    "student",
    "teacher"
  ],
  "files_that_disagree": [
    "audit-artifacts/module-completion/current/05_completion_scorecard.md",
    "docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv",
    "audit-artifacts/dashboard-completion/state/dashboard-certification-state.json"
  ],
  "factory_status": "factory output not found",
  "factory_files": [],
  "reconciliation_should_be_separate_pr": true
}
```

## Dashboard Rows

| dashboard_key | label | batch | route | summary_api | data_source_type | permission_proof_status | tenant_proof_status | browser_runtime_proof_status | evidence_packet_status | independent_review_or_workaround_status | matrix_row_status | state_register_status | final_classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attendance | Attendance | 1 | /attendance-dashboard | /api/v1/dashboards/attendance/summary | sample | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| billing | Billing | 1 | /billing-dashboard | /api/v1/dashboards/billing/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| financial-aid | Financial Aid | 2 | /financial-aid-dashboard | /api/v1/dashboards/financial-aid/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| registrar | Registrar | 1 | /registrar-dashboard | /api/v1/dashboards/registrar/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| scheduling | Scheduling | 3 | /scheduling-dashboard | /api/v1/dashboards/scheduling/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| gradebook | Gradebook | 1 | /gradebook-dashboard | /api/v1/dashboards/gradebook/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| student-care | Student Care | 2 | /student-care-dashboard | /api/v1/dashboards/student-care/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MISSING | MISSING | MISSING_PROOF |
| activities-athletics | Activities & Athletics | 2 | /activities-dashboard | /api/v1/dashboards/activities-athletics/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| communications | Communications | 1 | /communications-dashboard | /api/v1/dashboards/communications/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| school-administrator | School Administrator | 1 | /school-admin-dashboard | /api/v1/dashboards/school-administrator/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| school-board | School Board | 4 | /school-board-dashboard | /api/v1/dashboards/school-board/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| master-control | Master Control | 5 | /master-control-dashboard | /api/v1/dashboards/master-control/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| admissions | Admissions | 2 | /admissions-dashboard | /api/v1/dashboards/admissions/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| advancement | Advancement | 4 | /advancement-dashboard | /api/v1/dashboards/advancement/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| hr | HR | 3 | /hr-dashboard | /api/v1/dashboards/hr/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| facilities | Facilities | 3 | /facilities-dashboard | /api/v1/dashboards/facilities/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| health-office | Health Office | 3 | /health-office-dashboard | /api/v1/dashboards/health-office/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| transportation | Transportation | 3 | /transportation-dashboard | /api/v1/dashboards/transportation/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| food-service | Food Service | 3 | /food-service-dashboard | /api/v1/dashboards/food-service/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| it-support | IT Support | 3 | /it-support-dashboard | /api/v1/dashboards/it-support/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| fine-arts | Fine Arts | 4 | /fine-arts-dashboard | /api/v1/dashboards/fine-arts/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| athletics-director | Athletics Director | 5 | /athletics-director-dashboard | /api/v1/dashboards/athletics-director/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| library-media | Library / Media | 4 | /library-media-dashboard | /api/v1/dashboards/library-media/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| extended-care | Extended Care | 5 | /extended-care-dashboard | /api/v1/dashboards/extended-care/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| summer-camp | Summer Camp | 5 | /summer-camp-dashboard | /api/v1/dashboards/summer-camp/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| safety-security | Safety / Security | 3 | /safety-security-dashboard | /api/v1/dashboards/safety-security/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| curriculum-pd | Curriculum / PD Hub | 4 | /curriculum-pd-dashboard | /api/v1/dashboards/curriculum-pd/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| chaplain-spiritual-life | Chaplain / Spiritual Life | 4 | /chaplain-dashboard | /api/v1/dashboards/chaplain-spiritual-life/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| advancement-operations | Advancement Operations | 4 | /advancement-operations-dashboard | /api/v1/dashboards/advancement-operations/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| volunteer-management | Volunteer Management | 4 | /volunteer-management-dashboard | /api/v1/dashboards/volunteer-management/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| portrait-service | Portrait / Service Hours | 4 | /portrait-service-dashboard | /api/v1/dashboards/portrait-service/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| alumni-relations | Alumni Relations | 4 | /alumni-relations-dashboard | /api/v1/dashboards/alumni-relations/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| network-benchmarking | Network Benchmarking | 4 | /network-benchmarking-dashboard | /api/v1/dashboards/network-benchmarking/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| implementation-success | Implementation Success | 5 | /implementation-success-dashboard | /api/v1/dashboards/implementation-success/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| data-migration | Data Migration | 5 | /data-migration-dashboard | /api/v1/dashboards/data-migration/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| integrations-automation | Integrations / Automation | 5 | /integrations-automation-dashboard | /api/v1/dashboards/integrations-automation/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| compliance-audit | Compliance / Audit | 0 | /compliance-audit-dashboard | /api/v1/dashboards/compliance-audit/summary | fallback | PENDING | PENDING | frontend:PENDING;playwright:PENDING | present | pending | MAPPED | static_frontend_proof_truth_alignment_required_certification_blocked | MISSING_PROOF |
| revenue-operations | Revenue Operations | 5 | /revenue-operations-dashboard | /api/v1/dashboards/revenue-operations/summary | live | PENDING | PENDING | frontend:PENDING;playwright:PENDING | missing | pending | MAPPED | MISSING | MISSING_PROOF |
| release-reliability | Release Reliability | 0 | /release-reliability-dashboard | /api/v1/dashboards/release-reliability/summary | fallback | PENDING | PENDING | frontend:PENDING;playwright:PENDING | present | pending | MAPPED | truth_aligned_proof_in_progress_pending_independent_review | MISSING_PROOF |
| dashboard-certification-center | Dashboard Certification Center | 0 | /dashboard-certification-center | /api/v1/dashboards/dashboard-certification-center/summary | fallback | PENDING | PENDING | frontend:PENDING;playwright:PENDING | present | pending | MAPPED | proof_in_progress_certification_blocked | MISSING_PROOF |