# Static Frontend Proof: compliance-audit

Date: 2026-06-18
Dashboard key: compliance-audit
Evidence status: STATIC FRONTEND PROOF / TRUTH ALIGNMENT REQUIRED / NOT CERTIFIED

## Verified repository facts

- Page component exists: `frontend/dashboards/src/pages/ComplianceAuditDashboard.jsx`.
- Page renders `CrownDashboardTemplate`.
- Page uses template key `complianceAudit`.
- Page passes role key `complianceAudit`.
- Template exists: `frontend/dashboards/src/config/dashboardTemplates/complianceAuditDashboard.js`.
- Dashboard registry entry exists: `frontend/dashboards/src/config/dashboardRegistry.js`.
- Route path constant exists: `PATHS.COMPLIANCE_AUDIT_DASHBOARD` -> `/compliance-audit-dashboard`.
- Dashboard registry route generator wraps dashboards in `RoleRouteGuard` and `ReleaseStateRoute`.
- Main router spreads `...dashboardRoutes`.

## Static template observations

The template currently includes sample-like operational claims, including:

- 3 active audits.
- 86% controls passing.
- 4 open findings.
- 6 reviews due in 30 days.
- Diocese evidence package due April 13.
- SOC2 Type II fieldwork scheduled.

These values are presentation-ready but not yet proven as live compliance evidence in this dashboard certification lane.

## Required truth-alignment before certification

- Replace or clearly mark unverified compliance metrics.
- Wire the dashboard to a verifiable compliance control/evidence source.
- Prove active controls and finding source.
- Prove evidence-stream source.
- Prove review-due source.
- Add browser-rendered title/metrics proof.
- Add screenshot or trace artifact.
- Add role and tenant proof.
- Add independent review.

## Static frontend proof result

- Page component exists: PASS.
- Template exists: PASS.
- Route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- Truth alignment: REQUIRED.
- Browser/runtime proof: NOT VERIFIED.
- Certification: NOT CERTIFIED.

## Non-claims

This proof packet does not certify the dashboard.
This proof packet does not approve sandbox, pilot, production, or release GO.
