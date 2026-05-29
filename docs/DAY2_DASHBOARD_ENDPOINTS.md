# Day 2 Dashboard Endpoints

> Authority Scope Notice (2026-05-29)
>
> This file is an API operations reference and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

**Status**: Read-only dashboard APIs with tenant isolation
**Date**: January 27, 2026

---

## Overview

Three read-only dashboard endpoints providing high-level metrics for:
1. **Admissions funnel** - Application counts by status + 30-day trend
2. **Finance summary** - Billed/paid/outstanding totals
3. **Academics enrollment** - Student count + section distribution

All endpoints enforce tenant isolation per [TENANT_PRIVACY_CANON.md](TENANT_PRIVACY_CANON.md).

---

## Authentication & Tenant Context

### Required Headers
```http
Authorization: Bearer <JWT_TOKEN>
X-School-Id: <SCHOOL_UUID>
```

### Tenant Enforcement
- **Missing tenant**: Returns `400 Bad Request`
- **Invalid UUID**: Returns `400 Bad Request`
- **Wrong tenant (non-staff)**: Returns `404 Not Found`
- **Correct tenant**: Returns `200 OK` with school-scoped data

### Staff Override
Staff users can override tenant context by providing `X-School-Id` header explicitly.

---

## Endpoints

### 1. Admissions Funnel

```http
GET /api/v1/dashboards/admissions/funnel/
```

**Response**:
```json
{
  "school_id": "550e8400-e29b-41d4-a716-446655440000",
  "by_stage": [
    {"status": "SUBMITTED", "count": 42},
    {"status": "UNDER_REVIEW", "count": 18},
    {"status": "ACCEPTED", "count": 12},
    {"status": "WAITLISTED", "count": 5},
    {"status": "DENIED", "count": 3}
  ],
  "daily_30d": [
    {"day": "2026-01-01", "count": 5},
    {"day": "2026-01-02", "count": 3},
    {"day": "2026-01-03", "count": 7}
  ]
}
```

**Field Descriptions**:
- `by_stage`: Count of applications by current status
- `daily_30d`: Count of submitted applications per day (last 30 days)

**Example cURL** (PowerShell):
```powershell
$token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
$schoolId = "550e8400-e29b-41d4-a716-446655440000"

curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/admissions/funnel/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId" | ConvertFrom-Json | Format-List
```

---

### 2. Finance Summary

```http
GET /api/v1/dashboards/finance/summary/
```

**Response**:
```json
{
  "school_id": "550e8400-e29b-41d4-a716-446655440000",
  "billed_total": "125000.00",
  "paid_total": "98000.00",
  "outstanding_total": "27000.00"
}
```

**Field Descriptions**:
- `billed_total`: Sum of all invoice amounts for the school
- `paid_total`: Sum of all recorded payments for the school
- `outstanding_total`: `billed_total - paid_total`

**Example cURL** (PowerShell):
```powershell
$token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
$schoolId = "550e8400-e29b-41d4-a716-446655440000"

curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/finance/summary/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId" | ConvertFrom-Json | Format-List
```

---

### 3. Academics Enrollment

```http
GET /api/v1/dashboards/academics/enrollment/
```

**Response**:
```json
{
  "school_id": "550e8400-e29b-41d4-a716-446655440000",
  "active_students": 342,
  "active_sections": 48,
  "sections_by_term": [
    {"term": "2026-SPRING", "count": 25},
    {"term": "2026-FALL", "count": 23}
  ]
}
```

**Field Descriptions**:
- `active_students`: Total count of students for the school
- `active_sections`: Total count of course sections
- `sections_by_term`: Section count grouped by term (sorted descending)

**Note**: Attendance tracking will be added in a future iteration. This endpoint currently provides enrollment metrics.

**Example cURL** (PowerShell):
```powershell
$token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
$schoolId = "550e8400-e29b-41d4-a716-446655440000"

curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/academics/enrollment/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId" | ConvertFrom-Json | Format-List
```

---

## Error Responses

### Missing Tenant (400)
```json
{
  "school_id": ["Missing X-School-Id header (tenant context required)."]
}
```

### Invalid UUID (400)
```json
{
  "school_id": ["Invalid school_id UUID."]
}
```

### Wrong Tenant (404)
```json
{
  "detail": "Not found"
}
```

### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Testing

Run tenant isolation tests:
```powershell
cd backend
python manage.py test crown_api.tests.test_dashboard_tenant_isolation -v 2
```
Expected: **11/11 tests passing**

---

## Deployment Verification

After deploying Day 2 changes, verify all endpoints respond:

```powershell
# Get auth token
$auth = @{
  username = "admin"
  password = "your_password"
} | ConvertTo-Json

$token = (curl.exe -s https://crown-api-dev.azurewebsites.net/api/v1/auth/token/ `
  -H "Content-Type: application/json" `
  -d $auth | ConvertFrom-Json).access

$schoolId = "your-school-uuid"

# Test admissions funnel
curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/admissions/funnel/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId"

# Test finance summary
curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/finance/summary/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId"

# Test academics enrollment
curl.exe -s "https://crown-api-dev.azurewebsites.net/api/v1/dashboards/academics/enrollment/" `
  -H "Authorization: Bearer $token" `
  -H "X-School-Id: $schoolId"
```

All should return `200 OK` with JSON data.

---

## Academics Read-Only Spine APIs

**Scope:** Read-only only (no write endpoints).

**Endpoints:**
-
- `GET /api/v1/academics/years/`
- `GET /api/v1/academics/terms/`
- `GET /api/v1/academics/courses/`
- `GET /api/v1/academics/sections/`
- `GET /api/v1/academics/students/{id}/sections/`
- `GET /api/v1/academics/parents/me/students/`

**Pagination:** list endpoints support `limit` and `offset` (defaults: `limit=50`, `offset=0`).

**Filters:**
-
- `academic_year` or `academic_year_id`
- `term` (term code) or `term_id`
- `student_id`
- `teacher_id`

**Permissions matrix:**

| Role | Access |
| --- | --- |
| Head/Staff/Admin | All records within school |
| Teacher | Sections they teach + rosters |
| Parent | Their students + schedules |
| Student | Own schedule (requires identity mapping) |

**Seed expectations:**
-
- Script: `backend/scripts/seed_academics_readonly.py`
- Creates: 1 academic year, 2 terms, ~12 courses, ~20 sections, enrollments, teacher assignments
- Idempotent: safe to re-run locally

---

## Future Enhancements

1. **Attendance tracking**: Replace enrollment endpoint with real attendance metrics (present/absent/tardy)
2. **Caching**: Add Redis caching for frequently accessed dashboard data
3. **Time range filters**: Support `?start_date=` and `?end_date=` query params
4. **Pagination**: Add pagination for `daily_30d` trend data
5. **Real-time updates**: WebSocket support for live dashboard updates
6. **Drill-down**: Link to detailed views (e.g., list of applications in "SUBMITTED" status)

---

## Related Documentation

- [TENANT_PRIVACY_CANON.md](TENANT_PRIVACY_CANON.md) - Tenant isolation rules
- [RELEASE_NOTES.md](RELEASE_NOTES.md) - Release history
- [INVESTOR_STATEMENT.md](INVESTOR_STATEMENT.md) - Production status

---

## Implementation Details

**Files**:
- `backend/crown_api/dashboards/admissions.py` - Admissions funnel view
- `backend/crown_api/dashboards/finance.py` - Finance summary view
- `backend/crown_api/dashboards/academics.py` - Academics enrollment view
- `backend/crown_api/dashboards/urls.py` - URL routing
- `backend/crown_api/tests/test_dashboard_tenant_isolation.py` - Tenant isolation tests

**Dependencies**:
- `crown_api.dashboards.tenant.get_dashboard_school_id()` - Dashboard tenant helper (explicit header required)
- `admissions.models.AdmissionsApplication` - Application data
- `billing.models.Invoice` - Billing data
- `ledger.models.Payment` - Payment data
- `academics.models.Section` - Course section data
- `households.models.Student` - Student data
