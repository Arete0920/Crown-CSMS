# Admissions Funnel API Contract

**Version:** 1.0.0
**Status:** FROZEN (v1.0)
**Last Updated:** 2026-01-31
**Author:** @tcmegahan

---

## Base URLs

| Environment | URL |
|-------------|-----|
| **DEV** | `https://crown-api-dev.azurewebsites.net` |
| **PROD** | TBD (not yet deployed) |

---

## Authentication

All endpoints require:

- **Header:** `Authorization: Bearer <JWT_TOKEN>`
  Obtained from `POST /api/v1/auth/token/`

- **Header:** `X-School-Id: <UUID>`
  Required to scope all queries to school

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  -H "X-School-Id: $SCHOOL_ID" \
  https://crown-api-dev.azurewebsites.net/api/v1/admissions/summary/
```

---

## Endpoints

### 1. GET `/api/v1/admissions/summary/`

Returns one-screen KPI summary for admissions director.

**Query Parameters:**

| Param | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `academic_year` | string | No | Latest | Format: `YYYY-YYYY` |
| `date_from` | string | No | null | ISO 8601 date (YYYY-MM-DD) |
| `date_to` | string | No | null | ISO 8601 date (YYYY-MM-DD) |

**Example Request:**

```
GET /api/v1/admissions/summary/?academic_year=2025-2026
```

**Response (200 OK):**

```json
{
  "academic_year": "2025-2026",
  "date_from": null,
  "date_to": null,
  "pipeline": {
    "total": 120,
    "by_stage": {
      "inquiry": 55,
      "tour_scheduled": 20,
      "tour_completed": 12,
      "application_started": 14,
      "application_submitted": 10,
      "in_review": 4,
      "accepted": 3,
      "waitlisted": 1,
      "declined": 1,
      "enrolled": 2
    }
  },
  "conversion": {
    "inquiry_to_submitted": "0.18",
    "submitted_to_accepted": "0.30",
    "accepted_to_enrolled": "0.67"
  },
  "velocity_days": {
    "inquiry_to_tour_completed_avg": "7.50",
    "tour_completed_to_submitted_avg": "10.25",
    "submitted_to_decision_avg": "14.00"
  },
  "top_sources": [
    { "source": "church_referral", "total": 22 },
    { "source": "facebook", "total": 18 },
    { "source": "direct_mail_qr", "total": 15 }
  ]
}
```

**Response (empty results):**

```json
{
  "academic_year": "2025-2026",
  "date_from": null,
  "date_to": null,
  "pipeline": {
    "total": 0,
    "by_stage": {
      "inquiry": 0,
      "tour_scheduled": 0,
      "tour_completed": 0,
      "application_started": 0,
      "application_submitted": 0,
      "in_review": 0,
      "accepted": 0,
      "waitlisted": 0,
      "declined": 0,
      "enrolled": 0
    }
  },
  "conversion": {
    "inquiry_to_submitted": "0.00",
    "submitted_to_accepted": "0.00",
    "accepted_to_enrolled": "0.00"
  },
  "velocity_days": {
    "inquiry_to_tour_completed_avg": "0.00",
    "tour_completed_to_submitted_avg": "0.00",
    "submitted_to_decision_avg": "0.00"
  },
  "top_sources": []
}
```

**Field Notes:**

- `pipeline.total` = sum of all by_stage values
- `by_stage` always includes all enum keys (frozen stage names)
- `conversion` rates are **decimal strings** with exactly 2 decimal places
- Divide-by-zero cases → `"0.00"` (not null)
- `velocity_days` values are **decimal strings** with exactly 2 decimal places (average days between stage transitions)
- `top_sources` limited to top 3 by frequency; empty array if no leads
- Always returns same shape, even when empty

---

### 2. GET `/api/v1/admissions/drilldown/`

Returns paginated list of individual leads for drill-down inspection.

**Query Parameters:**

| Param | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `academic_year` | string | No | Latest | Format: `YYYY-YYYY` |
| `stage` | enum | No | All | One of: `inquiry`, `tour_scheduled`, `tour_completed`, `application_started`, `application_submitted`, `in_review`, `accepted`, `waitlisted`, `declined`, `enrolled` |
| `source` | string | No | All | Exact source value |
| `limit` | integer | No | `25` | Min: 1, Max: 200 |
| `offset` | integer | No | `0` | Min: 0 |

**Example Request:**

```
GET /api/v1/admissions/drilldown/?stage=inquiry&limit=25&offset=0
```

**Response (200 OK):**

```json
{
  "academic_year": "2025-2026",
  "stage": "inquiry",
  "source": null,
  "total": 55,
  "limit": 25,
  "offset": 0,
  "rows": [
    {
      "lead_id": "a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d",
      "application_id": "b8c9d0e1-f2a3-4b5c-6d7e-8f9a0b1c2d3e",
      "student_id": "c9d0e1f2-a3b4-5c6d-7e8f-9a0b1c2d3e4f",
      "stage": "inquiry",
      "source": "church_referral",
      "grade_applying_for": "5",
      "created_at": "2026-01-31T14:22:10Z",
      "updated_at": "2026-02-02T11:03:00Z",
      "flags": {
        "duplicate_suspected": false,
        "bot_suspected": false
      }
    }
  ]
}
```

**Response (empty results):**

```json
{
  "academic_year": "2025-2026",
  "stage": "accepted",
  "source": null,
  "total": 0,
  "limit": 25,
  "offset": 0,
  "rows": []
}
```

**Response (unfiltered - all stages):**

```json
{
  "academic_year": "2025-2026",
  "stage": null,
  "source": null,
  "total": 120,
  "limit": 25,
  "offset": 0,
  "rows": [
    {
      "lead_id": "a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d",
      "application_id": "b8c9d0e1-f2a3-4b5c-6d7e-8f9a0b1c2d3e",
      "student_id": "c9d0e1f2-a3b4-5c6d-7e8f-9a0b1c2d3e4f",
      "stage": "inquiry",
      "source": "facebook",
      "grade_applying_for": "8",
      "created_at": "2026-01-29T09:15:30Z",
      "updated_at": "2026-01-29T09:15:30Z",
      "flags": {
        "duplicate_suspected": false,
        "bot_suspected": false
      }
    }
  ]
}
```

**Field Notes:**

- `rows[]` represent **leads**; `application_id` and `student_id` can be null early in funnel (shape stays stable)
- `total` = total matching records (not just this page)
- `rows` = paginated results (max `limit` items)
- `stage` = null if not filtered, otherwise the filtered stage name
- `source` = null if not filtered, otherwise the filtered source
- `grade_applying_for` = grade as string (e.g., "5", "8")
- `flags` = always present object with boolean fields for data quality checks
- `created_at` = ISO 8601 timestamp (lead entry date)
- `updated_at` = ISO 8601 timestamp (last stage transition)
- Same shape returned even if `total=0` and `rows=[]`

**Pagination Example:**

```
# Page 1: fetch records 0-24
GET /api/v1/admissions/drilldown/?stage=inquiry&limit=25&offset=0
→ returns 25 rows if total >= 25

# Page 2: fetch records 25-49
GET /api/v1/admissions/drilldown/?stage=inquiry&limit=25&offset=25
→ returns up to 25 rows

# If offset >= total, returns empty rows but same shape
```

---

## Error Responses

### 400 Bad Request

**Invalid stage:**

```json
{
  "detail": "Invalid stage 'bogus'. Must be one of: inquiry, tour_scheduled, tour_completed, application_started, application_submitted, in_review, accepted, waitlisted, declined, enrolled."
}
```

**Invalid query parameters:**

```json
{
  "detail": "limit and offset must be integers"
}
```

Or field-specific errors:

```json
{
  "limit": ["A valid integer is required."]
}
```

**Missing required header:**

```json
{
  "detail": "Missing required header: X-School-Id"
}
```

### Auth Status Codes (Frozen Behavior)

| Scenario | Status | Example Response |
|----------|--------|------------------|
| Missing `Authorization` header | 403 | `{"detail": "Authentication credentials were not provided."}` |
| Invalid/expired token | 401 | `{"detail": "Invalid token"}` |
| Authenticated but permission denied (RBAC) | 403 | `{"detail": "You do not have permission to perform this action."}` |

Clients must branch on HTTP status code, **not** the `detail` message string.

---

## Enums

### AdmissionsStage

```typescript
type AdmissionsStage =
  | "inquiry"
  | "tour_scheduled"
  | "tour_completed"
  | "application_started"
  | "application_submitted"
  | "in_review"
  | "accepted"
  | "waitlisted"
  | "declined"
  | "enrolled";
```

### LeadSource

```typescript
type LeadSource =
  | "church_referral"
  | "facebook"
  | "instagram"
  | "google"
  | "direct_mail_qr"
  | "website"
  | "word_of_mouth"
  | "other";
```

---

## Full TypeScript Schema

```typescript
interface AdmissionsSummary {
  academic_year: string;
  date_from: string | null;
  date_to: string | null;
  pipeline: {
    total: number;
    by_stage: {
      [key in AdmissionsStage]: number;
    };
  };
  conversion: {
    inquiry_to_submitted: string; // Decimal string, 2 places
    submitted_to_accepted: string;
    accepted_to_enrolled: string;
  };
  velocity_days: {
    inquiry_to_tour_completed_avg: string; // Decimal string, 2 places
    tour_completed_to_submitted_avg: string;
    submitted_to_decision_avg: string;
  };
  top_sources: {
    source: LeadSource;
    total: number;
  }[];
}

interface AdmissionsDrilldown {
  academic_year: string;
  stage: AdmissionsStage | null;
  source: LeadSource | null;
  total: number;
  limit: number;
  offset: number;
  rows: {
    lead_id: string;
    application_id: string | null;
    student_id: string | null;
    stage: AdmissionsStage;
    source: LeadSource;
    grade_applying_for: string;
    created_at: string; // ISO 8601
    updated_at: string; // ISO 8601
    flags: {
      duplicate_suspected: boolean;
      bot_suspected: boolean;
    };
  }[];
}

type AdmissionsStage =
  | "inquiry"
  | "tour_scheduled"
  | "tour_completed"
  | "application_started"
  | "application_submitted"
  | "in_review"
  | "accepted"
  | "waitlisted"
  | "declined"
  | "enrolled";

type LeadSource =
  | "church_referral"
  | "facebook"
  | "instagram"
  | "google"
  | "direct_mail_qr"
  | "website"
  | "word_of_mouth"
  | "other";
```

---

## Backwards Compatibility

**Breaking changes** (would increment major version):

- Removing any top-level key
- Changing field type (e.g., string → number)
- Changing response structure (e.g., array → object)
- Removing enum values

**Non-breaking changes** (safe to roll out):

- Adding new optional keys
- Adding new enum values (LeadSource)
- Adding new stage enum values
- Changing error message text

---

## Testing This Contract

### Via curl

```bash
# Summary
curl -i \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-Id: $SCHOOL_ID" \
  https://crown-api-dev.azurewebsites.net/api/v1/admissions/summary/

# Drilldown with pagination
curl -i \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-Id: $SCHOOL_ID" \
  "https://crown-api-dev.azurewebsites.net/api/v1/admissions/drilldown/?stage=inquiry&limit=10&offset=0"
```

### Via PowerShell

```powershell
$API = "https://crown-api-dev.azurewebsites.net"
$token = (Invoke-RestMethod -Uri "$API/api/v1/auth/token/" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{username='head@crown-demo.local'; password=$env:CROWN_PASSWORD} | ConvertTo-Json -Compress)).access

$schoolId = "e5e7bec0-7e8a-4c8a-9b5c-7e8a4c8a9b5c"

# Summary
$summary = Invoke-RestMethod -Uri "$API/api/v1/admissions/summary/" `
  -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$schoolId}

# Drilldown
$drilldown = Invoke-RestMethod -Uri "$API/api/v1/admissions/drilldown/?stage=inquiry&limit=25&offset=0" `
  -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$schoolId}
```

---

## Contract Tests

This contract is **automatically enforced** by:
**`backend/admissions/tests/test_admissions_endpoints.py`**

- **12+ automated tests** validate every response shape, field type, and status code
- Tests fail if actual API behavior drifts from frozen contract
- Run locally: `python backend/manage.py test admissions.tests.test_admissions_endpoints`

**Example Test (Invalid Stage → 400):**
```python
def test_drilldown_invalid_stage_400(self):
    url = reverse("admissions:drilldown") + "?stage=INVALID"
    response = self.client.get(url, HTTP_X_SCHOOL_ID=str(self.school.id))
    self.assertEqual(response.status_code, 400)
    self.assertIn("stage", response.json()["detail"].lower())
```

These tests prevent "but the doc says..." bugs by ensuring the contract is **enforced in code**.

---

## Support

- **Issues:** See [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md)
- **Changes:** Coordinate with @tcmegahan before breaking edits
- **Smoke Tests:** Run `test_azure_smoke.ps1` post-deployment
