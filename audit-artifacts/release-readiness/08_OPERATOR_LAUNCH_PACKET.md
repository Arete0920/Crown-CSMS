# Operator Launch Packet

Generated: 2026-04-24
Gate: 12 (Operator Launch Packet)
Result: PASS

## Launch Targets
- Sandbox URL: https://crown-sandbox.azurestaticapps.net
- Backend API URL: https://crown-api-dev.azurewebsites.net
- Health endpoint: https://crown-api-dev.azurewebsites.net/api/health/

## School List
- Heritage Christian Academy
- Harvest Christian School
- Faith Christian Academy
- Calvary Christian School
- St. Anne's Academy

## Role List
- school admin
- registrar
- finance/billing user
- teacher
- parent

## Tester Instructions
1. Sign in with assigned sandbox persona.
2. Verify school context remains pinned to assigned school.
3. Execute role-appropriate workflows.
4. Confirm logout/session flow blocks protected routes post-logout.
5. Report defects with school, role, route, and screenshot.

## Completed Workflows (Certified)
- login/session
- school context
- school admin dashboard
- admissions
- enrollment handoff
- billing
- attendance
- registrar
- logout/session

Evidence source: audit-artifacts/sandbox-golden-path/00_STATUS.md

## Feedback Process
- Feedback form process: submit through #crown-sandbox-support using template
- Required fields: school, role, workflow, expected, actual, screenshot, severity

## Issue Reporting Process
- Intake: #crown-sandbox-support and support@crown2026.local
- Triage board owner: P. Ops
- Priority model: P0/P1/P2/P3 per support roster

## Support Escalation
- Escalation owner: T.C. Megahan
- Escalation path: Incident commander -> backend/frontend owner -> product communications
- Roster source: audit-artifacts/release-readiness/11_SUPPORT_TRIAGE_ROSTER.md

## Daily Triage Process
- 09:00 UTC: intake review and severity assignment
- 13:00 UTC: status checkpoint for open P0/P1 tickets
- 17:00 UTC: closure review and next-day handoff

## Gate Dependencies Closed
- Gate 7 evidence: audit-artifacts/release-readiness/03_DEPLOYMENT_READINESS_CHECKLIST.md
- Gate 8 evidence: audit-artifacts/release-readiness/10_ROLLBACK_DRILL_EVIDENCE.md
- Gate 9 evidence: audit-artifacts/release-readiness/11_SUPPORT_TRIAGE_ROSTER.md
- Gate 10 evidence: audit-artifacts/release-readiness/05_SANDBOX_DATA_SAFETY_SIGNOFF.md

## Operator Signoff
- Launch operator: T.C. Megahan
- Decision: APPROVED
- Signed at: 2026-04-24T23:59:30Z
