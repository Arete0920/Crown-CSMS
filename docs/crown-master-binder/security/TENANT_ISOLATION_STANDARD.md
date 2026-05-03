# CROWN Tenant Isolation Standard

Generated: 2026-04-30T18:21:35

## Rule

Every school-owned record must be scoped to the active school or tenant context on both
backend and frontend. Frontend filtering alone is not sufficient; backend enforcement is mandatory.

## Tenant-Sensitive Domains

Students, Households, Guardians/Parents, Staff/Faculty, Applicants, Enrollment,
Attendance, Grades, Transcripts, Billing (invoices/charges/payments/balances),
Communications (messages/announcements), Files/Documents, Courses/Sections/Rosters,
Dashboards and KPI aggregations.

## Required Enforcement

1. Backend querysets must filter by active tenant/school context.
2. Detail endpoints must reject cross-tenant ids.
3. List endpoints must return only active school data.
4. Create/update endpoints must assign or validate school context.
5. Delete/archive endpoints must verify school ownership.
6. Dashboard aggregations must be tenant-scoped.
7. File/document download endpoints must verify tenant ownership.
8. School switcher must reject unauthorized context switching.
9. RBAC and tenant isolation must both pass; one does not replace the other.

## Release Gate

No production GO until all TI-001 through TI-010 proof rows are PASS with evidence.

## Generated Evidence

Tenant signals:  C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\10_tenant_isolation_signals.csv
Bypass risks:    C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\11_possible_tenant_bypass_risks.csv
API signals:     C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\12_api_view_signals.csv
Perm signals:    C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\13_permission_signals.csv
Entity map:      C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\14_tenant_sensitive_entity_map.csv
Proof matrix:    C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\15_tenant_isolation_manual_proof_matrix.csv
High-risk rows:  C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\16_high_risk_tenant_review_rows.csv
Blocker board:   C:\w\crown_main_postmerge_verify\audit-artifacts\priority-04-tenant-isolation\20260430_182109\17_TENANT_ISOLATION_BLOCKER_BOARD.csv
