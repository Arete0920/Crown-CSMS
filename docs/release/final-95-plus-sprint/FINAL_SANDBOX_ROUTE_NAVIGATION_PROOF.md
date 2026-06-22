# CROWN Sandbox Route & Navigation Proof - 2026-06-22

**Status**: Frontend routing and navigation candidate validation

## Primary sandbox routes

| Path | Purpose | Access | Proof status |
|------|---------|--------|--------------|
| `/` | Home/login redirect | Public | Release verify smoke candidate |
| `/public/admissions/apply` | New family workflow | Public | Admissions route registration candidate |
| `/public/admissions/status` | Application status lookup | Public | Admissions route registration candidate |
| `/dashboard/home` | User home dashboard | Auth | Dashboard route candidate |
| `/dashboard/admissions` | Admissions director view | Auth + Role | Dashboard route candidate |
| `/dashboard/attendance` | Attendance dashboard | Auth + Role | Dashboard route candidate |
| `/dashboard/billing` | Billing/aid dashboard | Auth + Role | Dashboard route candidate |
| `/dashboard/gradebook` | Gradebook dashboard | Auth + Role | Dashboard route candidate |
| `/dashboard/communications` | Communications hub | Auth + Role | Dashboard route candidate |
| `/dashboard/registrar` | Registrar operations | Auth + Role | Dashboard route candidate |

## New Batch 5 dashboards

- `/dashboard/data-migration` - Data import and migration monitoring
- `/dashboard/integrations-automation` - Third-party system integrations
- `/dashboard/revenue-operations` - Revenue and pricing analytics
- `/dashboard/summer-camp` - Summer program command center
- `/dashboard/extended-care` - Before/after school care
- `/dashboard/athletics-director` - Athletic department oversight

**Backend API evidence**: `backend/crown_api/tests/test_batch5_remaining_dashboard_summary_api.py` verifies Batch 5 summary API authentication, tenant header, cross-tenant rejection, and payload behavior. It does not by itself prove sidebar rendering, breadcrumbs, ARIA behavior, or browser link exposure.

## Navigation surface claim boundary

- Sidebar role rendering: candidate until same-SHA frontend/browser evidence confirms it.
- Breadcrumb rendering: candidate until same-SHA frontend/browser evidence confirms it.
- Cross-tenant link exposure: candidate until same-SHA browser evidence confirms it.
- Accessibility labels: not verified by the backend API test file.

## Route protection

| Route class | Unauthenticated | Wrong role | Cross-tenant | Evidence status |
|-------------|-----------------|------------|--------------|-----------------|
| dashboard summary API | 401 | existing auth gate | 403/404 for strict tenant dashboards | Batch 5 backend API tests |
| public admissions paths | public | public | school selection dependent | Route registration candidate |

## Smoke test results

Local smoke evidence was reported for `npm run test:e2e:smoke`. Final status requires same-SHA CI and post-merge verification.

## Known limitations

- Custom integrations show placeholders or sandbox data.
- External report generation uses sandbox data only.
- Third-party webhooks are not active in sandbox.

## Next validation

After merge: run full role journey matrix against the deployed sandbox instance.
