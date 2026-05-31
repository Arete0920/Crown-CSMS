# CROWN Final 95+ Route / API / Role / Data Audit - 2026-05-30

Status: CONNECTOR-BACKED AUDIT ARTIFACT
Authority: Non-shipping audit document until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This artifact captures connector-backed findings for the four highest-risk wiring categories in the final 95+ sprint:

1. Frontend route exposure.
2. API canonicalization and compatibility routing.
3. Role vocabulary and permission mapping.
4. Dashboard/wizard data readiness and release-state truth.

It does not claim runtime pass. Local/CI proof is still required.

## 1. Frontend route exposure

### Verified structure

Dashboard routes are generated from `DASHBOARD_REGISTRY` and wrapped with both:

- `RoleRouteGuard`
- `ReleaseStateRoute`

This is a strong architectural pattern because registry dashboards can be centrally permissioned and release-gated.

Wizard routes are generated from `WIZARD_ROUTE_DEFINITIONS` and wrapped with:

- `ReleaseStateRoute`
- `RoleRouteGuard` when roles are present

This is also a strong pattern.

### Remaining risk

`frontend/dashboards/src/routes/router.jsx` still contains manual routes outside the generated dashboard/wizard path. Manual routes must be classified one by one:

- public route,
- sandbox-only route,
- launch-preview route,
- role-guarded route,
- release-gated route,
- defect.

### Required closure artifact

`docs/release/final-95-plus-sprint/FINAL_ROUTE_GUARD_AUDIT.md`

Minimum required columns:

| Route | Component | Public/Sensitive | Guard | Release Gate | Status | Evidence |
|---|---|---|---|---|---|---|

### PASS condition

Every sensitive route is guarded or release-gated. Every public route is explicitly classified as public. No route is left ambiguous.

## 2. API canonicalization

### Verified structure

`backend/crown_api/api_v1_urls.py` includes explicit `/api/v1` surfaces for admissions, learning continuity, telemetry, transcript probes, exports, academics, gradebook, households, billing, financial aid, payments, platform/operations modules, parent360, aftercare, summer camp, home academy, M365, and then a legacy `crown_api.api_urls` catch-all.

The ordering comment indicates specific module includes are intentionally placed before the legacy catch-all to avoid route shadowing.

### Remaining risk

A legacy catch-all is useful for compatibility but risky for final 95+ certification unless every route is inventoried and classified.

Frontend API clients still need a full audit for mixed prefixes:

- `/api/v1/...` canonical paths.
- `/api/...` compatibility paths.
- any noncanonical route that should be migrated or explicitly documented.

### Required closure artifact

`docs/release/final-95-plus-sprint/FINAL_API_CONTRACT_AUDIT.md`

Minimum required columns:

| Frontend client | Called path | Backend route | Canonical/compatibility | Auth/Tenant/RBAC | Test | Status |
|---|---|---|---|---|---|---|

### PASS condition

Every frontend API path maps to a backend route and has contract proof. Production-facing routes are canonical `/api/v1` unless documented as compatibility aliases.

## 3. Role vocabulary and permission mapping

### Verified structure

Frontend role handling contains:

- `ROLE_GROUPS` for route guard groups.
- `ROLE_EQUIVALENCE_GROUPS` and `ROLE_ALIAS_LOOKUP` for normalization.
- `normalizeRoles`, `hasAnyRole`, `hasAllRoles`, and `isAccessAllowed` helpers.
- Nav filtering that considers roles, allowedRoles, permissions, and visible children.

This is a strong start. The role alias layer reduces backend/frontend vocabulary drift.

### Remaining risk

Final 95+ certification still requires an explicit backend-to-frontend role matrix:

- backend role codes,
- frontend aliases,
- navigation visibility,
- route access,
- API permission codes,
- object-level access expectations.

### Required closure artifact

`docs/release/final-95-plus-sprint/FINAL_ROLE_PERMISSION_MATRIX.md`

Minimum required columns:

| Canonical Role | Backend Code(s) | Frontend Alias(es) | Dashboard Access | Wizard Access | API Permissions | Test Evidence | Status |
|---|---|---|---|---|---|---|---|

### PASS condition

Every production role has a deterministic mapping from backend identity to frontend routing/nav/API permissions, and negative tests prove blocked access.

## 4. Dashboard and wizard release-state truth

### Verified structure

The repo has a release-state model with states:

- `ready`
- `live`
- `production`
- `draft`
- `placeholder`
- `coming_soon`
- `hidden`
- `disabled`

Ready-like states are explicitly limited to `ready`, `live`, and `production`.

The module readiness engine can detect fake-ready routes by checking:

- missing required fields,
- missing concrete component,
- missing readiness flags,
- false readiness flags,
- placeholder signals on ready routes,
- invalid paths,
- duplicate ready module keys.

This is a strong anti-phantom-module control.

### Remaining risk

The readiness engine must be run on the current candidate SHA and its results committed. Presence in a registry is not enough.

Dashboard registry entries default to `draft` unless explicitly marked ready-like. Wizard definitions also default to `draft`, with placeholder entries guarded by release-state routing.

### Required closure artifacts

1. `docs/release/final-95-plus-sprint/FINAL_DASHBOARD_KPI_PROVENANCE_MATRIX.md`
2. `docs/release/final-95-plus-sprint/FINAL_WIZARD_COMPLETION_MATRIX.md`
3. `docs/release/final-95-plus-sprint/FINAL_MODULE_READINESS_PROOF.md`

Minimum dashboard columns:

| Dashboard | Release State | Readiness Flags | KPI Source | Data State | Route Guard | API Contract | Test | Status |
|---|---|---|---|---|---|---|---|---|

Minimum wizard columns:

| Wizard | Release State | API Prefix | Role Guard | Backend Session API | End-to-End Test | Status |
|---|---|---|---|---|---|

### PASS condition

No production dashboard or wizard is placeholder/fake-ready. Every production surface has full data provenance and route/API proof.

## Immediate local commands that close this audit

Run the proof pack in:

`docs/release/final-95-plus-sprint/VSCODE_COMMAND_PACK_20260530.md`

Pay special attention to:

- `npm run check:shell-certification`
- `npm run check:shell-backend-contract-parity`
- `npm run verify:dashboard-completeness`
- `node scripts/release/verify-api-contracts.mjs`
- `node scripts/release/verify-navigation-surface.mjs`

## Current status

| Area | Status |
|---|---|
| Generated dashboard route pattern | STRONG / PRESENT |
| Generated wizard route pattern | STRONG / PRESENT |
| Manual route audit | NOT DONE |
| API canonicalization audit | NOT DONE |
| Backend/frontend role matrix | NOT DONE |
| Dashboard KPI provenance matrix | NOT DONE |
| Wizard completion matrix | NOT DONE |
| Runtime proof on current candidate | NOT DONE |

## Release impact

Until this audit is closed with evidence, route/API/role/data readiness remains below the required 95+ production threshold.
