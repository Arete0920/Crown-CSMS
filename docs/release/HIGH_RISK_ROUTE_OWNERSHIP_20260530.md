# High-Risk Route Ownership Tags

Date: 2026-05-30
Purpose: assign explicit ownership tags to high-risk guarded routes.

| Route | Risk Class | Guard Type | Owner Tag |
| --- | --- | --- | --- |
| PATHS.STUDENT | Student privacy + access | RoleRouteGuard | owner:student-platform |
| /student/dashboard | Student privacy + access | RoleRouteGuard | owner:student-platform |
| /student/today | Student learning data | RoleGuard | owner:academics-platform |
| /student/assignments | Student learning data | RoleGuard | owner:academics-platform |
| /parent/attendance | Family attendance visibility | RoleRouteGuard | owner:family-platform |
| /teacher/attendance | Staff attendance operations | RoleGuard | owner:academics-platform |
| /summer-camp | Program operations and roster integrity | RoleRouteGuard | owner:extended-care-platform |
| /summer-camp/roster | Program operations and roster integrity | RoleRouteGuard | owner:extended-care-platform |

Enforcement:
- scripts/release/verify_high_risk_route_ownership.ps1
