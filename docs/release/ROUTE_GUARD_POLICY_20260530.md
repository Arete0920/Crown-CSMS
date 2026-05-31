# Route Guard Policy (Deny-by-Default)

Date: 2026-05-30
Purpose: enforce deny-by-default guard posture for sensitive route groups.

Policy statements:
- Any sensitive route must be wrapped by RoleGuard or RoleRouteGuard.
- Routes without explicit guard wrappers are treated as non-sensitive/public-only paths.
- Student direct routes must remain RoleRouteGuard with allowedRoles ["student"].
- Parent-only sensitive routes must remain RoleRouteGuard with allowedRoles ["parent"].

Sensitive route groups:
- Student direct: PATHS.STUDENT, /student/dashboard
- Student learning: /student/today, /student/assignments
- Parent attendance: /parent/attendance
- Teacher attendance: /teacher/attendance
- Summer camp operations: /summer-camp, /summer-camp/roster

Enforcement:
- scripts/release/verify_route_guard_policy.ps1
- frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx
