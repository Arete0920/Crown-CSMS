# Student-Facing Route Guard Inventory

Date: 2026-05-30
Purpose: inventory current student-facing routes and assert guard strategy.

Guard strategy:
- Direct student dashboard routes must use RoleRouteGuard with allowedRoles ["student"].
- Student learning workflow routes are guarded by RoleGuard with STUDENT_LEARNING_ALLOWED_ROLES.
- Parent student-detail routes remain parent-only and are not treated as direct student routes.

## Student-Facing Routes

| Route | Guard Type | Allowed Roles Source | Expected Component |
| --- | --- | --- | --- |
| PATHS.STUDENT | RoleRouteGuard | ["student"] | StudentDashboard |
| /student/dashboard | RoleRouteGuard | ["student"] | StudentDashboard |
| /student/today | RoleGuard | STUDENT_LEARNING_ALLOWED_ROLES | StudentTodayPage |
| /student/assignments | RoleGuard | STUDENT_LEARNING_ALLOWED_ROLES | StudentTodayPage |

Evidence:
- frontend/dashboards/src/routes/router.jsx
- frontend/dashboards/src/tests/releaseHardeningContracts.test.jsx
- scripts/release/verify_student_route_inventory.ps1
