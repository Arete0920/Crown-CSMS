# Dashboard Evidence Packet: release-reliability

Dashboard key: release-reliability
Module key: release-reliability
Owner: TBD
Independent reviewer: TBD
Status: MAPPED / STATIC_FRONTEND_PROOF / TRUTH_ALIGNMENT_REQUIRED / CERTIFICATION_BLOCKED
Date: 2026-06-18
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Static frontend proof: audit-artifacts/dashboard-completion/frontend-proof/batch0/release-reliability-static-proof-20260618.md

## Current proof summary

- Backend sample payload exists: PASS.
- Frontend page exists: PASS.
- Frontend template exists: PASS.
- Frontend route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- Truth alignment: REQUIRED.
- API permission proof: NOT VERIFIED.
- Tenant proof: NOT VERIFIED.
- Browser-rendered title/metrics proof: NOT VERIFIED.
- Screenshot or trace: NOT PROVIDED.
- Independent review: PENDING.
- Matrix promotion: NOT DONE.

## Contract

- Contract path: docs/dashboard-completion/contracts/batch0/release-reliability.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: deployment count, open production incidents, failed checks, release readiness
- Alert definitions: contract gate failure, build SHA mismatch, incomplete release proof packet
- Queue/list definitions: gate review queue, environment alignment queue, incident postmortem queue, readiness summary queue
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## Static frontend proof

Connector inspection verified:

- `frontend/dashboards/src/pages/ReleaseReliabilityDashboard.jsx` exists.
- Page renders `CrownDashboardTemplate`.
- Page uses template key `releaseReliability`.
- Template file exists at `frontend/dashboards/src/config/dashboardTemplates/releaseReliabilityDashboard.js`.
- Registry path exists at `frontend/dashboards/src/config/dashboardRegistry.js`.
- Route path resolves to `/release-reliability-dashboard`.
- Dashboard registry route generator wraps dashboards in `RoleRouteGuard` and `ReleaseStateRoute`.
- Main router includes `...dashboardRoutes`.

## Truth-alignment blocker

The current template contains presentation-ready sample claims that are not yet proven as live release evidence in this certification lane, including deployment counts, uptime, incident count, MTTR, and hotfix status.

Before certification, these values must be either backed by a verifiable release state source or clearly marked as scaffold/fallback data.

## Required next proof

- Wire or document release truth source.
- Prove summary API authentication and permission behavior.
- Prove tenant isolation behavior.
- Capture browser-rendered title and metrics proof.
- Capture screenshot or trace artifact.
- Assign valid owner and independent reviewer.
- Complete independent review.
- Promote matrix only after proof is complete.

## Certification decision

- Matrix row updated: not yet.
- Status promoted to: not yet.
- Certification: NOT CERTIFIED.

## Non-claims

This packet does not certify the dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
