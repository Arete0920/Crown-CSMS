# CROWN Frontend Route Source Ledger

**Document ID:** CROWN-GOV-010  
**Status:** ACTIVE — Stage 1 frontend route-source census  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Baseline repository SHA:** `4332f4cd0839d095e1c9ca0d6b8925bcd3370bf7`  
**Verification date:** 2026-07-25  
**Controlling issue:** #1587

## Purpose

Establish the controlled source ownership, generation path, access wrapper, release-state wrapper, and unresolved proof obligations for the active CROWN frontend route surface. This ledger inventories route construction only. It does not certify page functionality, backend authorization, tenant isolation, deployed runtime behavior, or production readiness.

## Route-source hierarchy

| Source | Ownership | Route construction | Primary controls | Current disposition |
|---|---|---|---|---|
| `frontend/dashboards/src/routes/router.jsx` | Explicit application routes and aliases | Static route objects plus generated route collections | `RoleGuard`, `RoleRouteGuard`, `ParentJourneyRouteGuard`, `RequirePermission`, environment switches, redirects | ACTIVE; exact row-level census still required |
| `frontend/dashboards/src/routes/dashboardRoutes.jsx` | Dashboard registry-generated routes | Maps `DASHBOARD_REGISTRY` entries to route objects | `RoleRouteGuard`; `ReleaseStateRoute` outside sandbox | ACTIVE generated surface |
| `frontend/dashboards/src/routes/wizards.js` | Wizard registry-generated routes | Maps 28 normalized wizard definitions to route objects | `RoleRouteGuard`; `ReleaseStateRoute` | ACTIVE generated surface |
| `frontend/dashboards/src/routes/paths.*` | Canonical path constants | Supplies path values to explicit routes | Indirect; depends on consuming route wrapper | ACTIVE shared path authority |
| `frontend/dashboards/src/routes/routeGroups.*` | Shared role groups | Supplies role arrays to route guards | `RoleGuard` and `RoleRouteGuard` consumers | ACTIVE shared access vocabulary |

## Verified generated-route controls

### Dashboard routes

`dashboardRoutes.jsx` creates one route per `DASHBOARD_REGISTRY` entry.

- The route path comes from `dashboard.path`.
- The page component comes from `dashboard.component`.
- Allowed roles come from `dashboard.roles` or `dashboard.allowedRoles`.
- Every generated dashboard route is wrapped by `RoleRouteGuard`.
- Outside sandbox mode, each dashboard route is additionally wrapped by `ReleaseStateRoute`.
- In sandbox mode, the release-state wrapper is bypassed and the dashboard component is rendered directly after the role guard.

This is source-level wiring evidence only. It does not prove backend permission parity, tenant scope, current release evidence, or deployed browser behavior.

### Wizard routes

`wizards.js` defines and normalizes 28 wizard route records before generating route objects.

- Each definition includes a frontend path, component, display name, API prefix, and role list.
- `releaseState` defaults to `draft` when omitted.
- Readiness defaults to incomplete placeholders unless the route is marked ready-like.
- Every generated wizard route is wrapped by `ReleaseStateRoute`.
- Wizard routes with role lists are additionally wrapped by `RoleRouteGuard`.
- Several wizard definitions reference historical evidence from 2026-06-14 and candidate SHA `8097d4c23e847bfaced4d9a49637a3aa0e20617b`; that evidence is not current-main certification.

## Explicit route classes in `router.jsx`

| Class | Verified examples | Primary frontend control | Open proof obligation |
|---|---|---|---|
| Public and authentication | `/login`, `/logout`, admissions start/apply/checklist | Public route or redirect | Confirm intended unauthenticated boundary and negative behavior |
| Root and role landing | `/`, `/dashboard`, `/dash/:role` | Redirect, launch-preview switch, or role dashboard component | Prove role resolution and backend identity parity |
| Teacher workflows | attendance, daily cockpit, lesson plans, classes, curriculum, scheduling aliases | `RoleGuard` with academic role groups | Verify backend permissions, section scope, and tenant scope |
| Parent workflows | attendance, billing, aid, lifecycle, learning status, communications and scheduling aliases | `RoleRouteGuard` plus `ParentJourneyRouteGuard` where applicable | Verify guardian/student relationship scope and direct-route denial |
| Student workflows | student dashboard, today, assignments | `RoleRouteGuard` or shared learning role group | Verify student identity restriction and cross-student denial |
| Finance workflows | billing, invoices, payment methods, exports, exceptions | `RequirePermission` or finance role lists | Reconcile role-list authorization with backend permission contracts |
| Academic workflows | academics, gradebook, transcript, category weights, interventions | `RoleGuard` and mixed family-view inclusion | Verify read/write boundaries and record-level scope |
| Administrative surfaces | school administration, master control, settings, reporting, status/readiness | Mixed role and permission wrappers; some direct components | Identify unwrapped privileged pages and prove backend enforcement |
| Module dashboards | finance, IT, marketing, spiritual life, office, health, counseling, food, athletics, advancement, transportation, facilities, security, and others | Mixed explicit route objects and generated dashboard routes | Reconcile duplicate paths, canonical ownership, and release-state behavior |
| Sandbox and launch preview | sandbox landing, command center, launch dashboard/module pages | Environment switches | Prove production exclusion and no unintended fallback |
| Compatibility aliases | teacher, parent, billing, admin, students/families/staff/reports/enrollment aliases | Redirects or duplicate wrappers | Decide retain-versus-retire and bind canonical targets |
| Error and denial | not-authorized, forbidden, not-found | Dedicated pages | Verify direct URL and unknown-route behavior |

## Controlled findings

1. Frontend route ownership is split among explicit routes, dashboard-generated routes, wizard-generated routes, shared path constants, and shared role groups.
2. Access controls are not uniform: the route surface uses role groups, literal role lists, permission wrappers, parent-journey guards, release-state wrappers, redirects, and environment switches.
3. Sandbox mode intentionally bypasses dashboard `ReleaseStateRoute` checks after role validation; this requires explicit production-exclusion proof.
4. Wizard readiness metadata includes historical evidence and must not be treated as current-main certification.
5. Several module/persona pages are mounted directly without an obvious route-level role or permission wrapper in `router.jsx`; backend enforcement may still exist, but route-level absence must be reconciled rather than inferred safe.
6. Compatibility aliases and duplicate route families remain active and require canonical ownership decisions.
7. The current source contains malformed replacement characters in comments. This is source hygiene noise, not established runtime behavior.

## Required next evidence

1. Generate an exact row-level manifest for every explicit, dashboard-generated, and wizard-generated frontend route.
2. Resolve every `PATHS.*` constant to its concrete path.
3. Record component, route source, guard type, allowed roles/permission, release-state wrapper, environment condition, alias target, and backend dependency for each route.
4. Identify route collisions and duplicate canonical/alias ownership.
5. Compare frontend role and permission controls with backend endpoint authorization and tenant boundaries.
6. Run direct-route negative browser tests for parent, student, teacher, finance, board, administrator, and unauthenticated personas.
7. Prove sandbox and launch-preview paths are excluded or fail closed in production configuration.
8. Replace historical readiness references with current-SHA evidence or mark them explicitly stale/unknown.

## Release authority

This ledger improves source traceability only. It does not authorize production, certify any dashboard or wizard, or establish buyer readiness. Production remains **NOT APPROVED**.
