# Financial Aid API Contract (Frozen)

**Last Updated:** 2026-01-31  
**Status:** FROZEN – No breaking changes without major version bump  
**Base URL (DEV):** `https://crown-api-dev.azurewebsites.net`  
**Base URL (PROD):** TBD (not yet deployed)

---

## Authentication & Headers

All endpoints require:

| Header | Type | Required | Example |
|--------|------|----------|---------|
| `Authorization` | Bearer token | Yes | `Bearer eyJhbGc...` |
| `X-School-Id` | UUID | Yes | `e5e7bec0-7e8a-4c8a-9b5c-7e8a4c8a9b5c` |

**Error if missing:**
- Missing/invalid `Authorization` → `403 Forbidden` (observed behavior; not JWT-standard 401)
- Missing/invalid `X-School-Id` → `400 Bad Request`

---

## Enums

### AidBucket

```
"need"       → Need-based financial aid
"mission"    → Mission-driven awards
"marketing"  → Marketing/enrollment incentives
"merit"      → Merit-based awards
"hardship"   → Hardship or emergency aid
```

### Application Status

```
"draft"      → Not yet submitted
"submitted"  → Submitted, awaiting review
"in_review"  → Under review by staff
"decided"    → Decision made (approved/denied)
```

---

## Endpoints

### 1. GET `/api/v1/financial-aid/summary/`

Returns aggregate financial aid data for a school and academic year.

**Query Parameters:**

| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `academic_year` | string | No | Latest available | Format: `YYYY-YYYY` e.g. `2025-2026` |

**Response (200 OK):**

```json
{
  "academic_year": "2025-2026",
  "applications": {
    "total": 10,
    "by_status": {
      "draft": 2,
      "submitted": 3,
      "in_review": 2,
      "decided": 3
    }
  },
  "awards": {
    "total": 24,
    "total_amount": "85000.00",
    "avg_amount": "3541.67",
    "by_bucket": {
      "need": {
        "total": 6,
        "amount": "25000.00"
      },
      "mission": {
        "total": 4,
        "amount": "15000.00"
      },
      "marketing": {
        "total": 5,
        "amount": "20000.00"
      },
      "merit": {
        "total": 5,
        "amount": "18000.00"
      },
      "hardship": {
        "total": 4,
        "amount": "7000.00"
      }
    }
  }
}
```

**Response (empty year):**

```json
{
  "academic_year": "2025-2026",
  "applications": {
    "total": 0,
    "by_status": {
      "draft": 0,
      "submitted": 0,
      "in_review": 0,
      "decided": 0
    }
  },
  "awards": {
    "total": 0,
    "total_amount": "0.00",
    "avg_amount": "0.00",
    "by_bucket": {
      "need": {"total": 0, "amount": "0.00"},
      "mission": {"total": 0, "amount": "0.00"},
      "marketing": {"total": 0, "amount": "0.00"},
      "merit": {"total": 0, "amount": "0.00"},
      "hardship": {"total": 0, "amount": "0.00"}
    }
  }
}
```

**Field Notes:**

- All amounts are **decimal strings** with exactly 2 decimal places
- `total` = count of items
- `avg_amount` is only calculated if `awards.total > 0`
- Always returns same shape, even when empty

---

### 2. GET `/api/v1/financial-aid/drilldown/`

Returns paginated list of individual awards for drill-down inspection.

**Query Parameters:**

| Param | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `academic_year` | string | No | Latest | Format: `YYYY-YYYY` |
| `bucket` | enum | No | All | One of: `need`, `mission`, `marketing`, `merit`, `hardship` |
| `limit` | integer | No | `25` | Min: 1, Max: 200 |
| `offset` | integer | No | `0` | Min: 0 |

**Example Request:**

```
GET /api/v1/financial-aid/drilldown/?bucket=need&limit=25&offset=0
```

**Response (200 OK):**

```json
{
  "academic_year": "2025-2026",
  "bucket": "need",
  "total": 6,
  "limit": 25,
  "offset": 0,
  "rows": [
    {
      "award_id": "a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d",
      "application_id": "b8c9d0e1-f2a3-4b5c-6d7e-8f9a0b1c2d3e",
      "household_id": "c9d0e1f2-a3b4-5c6d-7e8f-9a0b1c2d3e4f",
      "bucket": "need",
      "amount": "2500.00",
      "application_status": "decided",
      "award_status": "awarded",
      "rationale": "Outstanding merit and demonstrated need",
      "updated_at": "2026-01-31T14:22:10Z"
    }
  ]
}
```

**Response (empty results):**

```json
{
  "academic_year": "2025-2026",
  "bucket": "hardship",
  "total": 0,
  "limit": 25,
  "offset": 0,
  "rows": []
}
```

**Response (unfiltered - all buckets):**

```json
{
  "academic_year": "2025-2026",
  "bucket": null,
  "total": 24,
  "limit": 25,
  "offset": 0,
  "rows": [
    {
      "award_id": "a7b8c9d0-e1f2-3a4b-5c6d-7e8f9a0b1c2d",
      "application_id": "b8c9d0e1-f2a3-4b5c-6d7e-8f9a0b1c2d3e",
      "household_id": "c9d0e1f2-a3b4-5c6d-7e8f-9a0b1c2d3e4f",
      "bucket": "need",
      "amount": "2500.00",
      "application_status": "decided",
      "award_status": "awarded",
      "rationale": "Outstanding merit and demonstrated need",
      "updated_at": "2026-01-31T14:22:10Z"
    }
  ]
}
```

**Field Notes:**

- `rows[]` represent **awards**; `application_id` is the associated financial aid application
- `total` = total matching records (not just this page)
- `rows` = paginated results (max `limit` items)
- `bucket` = null if not filtered, otherwise the filtered bucket name
- `application_status` = one of: `draft`, `submitted`, `in_review`, `decided`
- `award_status` = one of: `awarded`, `denied`, `revised`, `withdrawn`
- `rationale` = null if not provided, otherwise text
- `updated_at` = ISO 8601 timestamp
- Amount is always a **decimal string** with 2 decimal places
- Same shape returned even if `total=0` and `rows=[]`

**Pagination Example:**

```
# Page 1: fetch records 0-24
GET /api/v1/financial-aid/drilldown/?bucket=need&limit=25&offset=0
→ returns 25 rows if total >= 25

# Page 2: fetch records 25-49
GET /api/v1/financial-aid/drilldown/?bucket=need&limit=25&offset=25
→ returns up to 25 rows

# If offset >= total, returns empty rows but same shape
```

---

## Error Responses

### 400 Bad Request

**Invalid bucket:**

```json
{
  "detail": "Invalid bucket 'bogus'. Must be one of: need, mission, marketing, merit, hardship."
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

## Money Format

All monetary amounts are **decimal strings** with exactly 2 decimal places:

- ✅ Valid: `"100.00"`, `"0.00"`, `"3541.67"`
- ❌ Invalid: `"100"`, `"100.0"`, `100` (number)

This ensures precision across frontend, backend, and downstream systems.

---

## Pagination Strategy

For "Load More" UI patterns:

1. **Initial load:** `limit=25&offset=0`
2. **Each "load more" click:** Increment `offset` by `limit`
3. **Stop loading when:** `len(rows) < limit`

Example:

```python
# Python pseudo-code
offset = 0
while True:
    resp = get_drilldown(bucket="need", limit=25, offset=offset)
    display_rows(resp['rows'])
    if len(resp['rows']) < resp['limit']:
        break  # No more records
    offset += resp['limit']
```

---

## Schema Validation (TypeScript)

```typescript
// For frontend type safety
interface FinancialAidSummary {
  academic_year: string;
  applications: {
    total: number;
    by_status: {
      draft: number;
      submitted: number;
      in_review: number;
      decided: number;
    };
  };
  awards: {
    total: number;
    total_amount: string; // Decimal string
    avg_amount: string;   // Decimal string
    by_bucket: {
      [key in AidBucket]: {
        total: number;
        amount: string; // Decimal string
      };
    };
  };
}

interface FinancialAidDrilldown {
  academic_year: string;
  bucket: AidBucket | null;
  total: number;
  limit: number;
  offset: number;
  rows: {
    award_id: string;
    application_id: string;
    household_id: string | null;
    bucket: AidBucket;
    amount: string; // Decimal string
    application_status: "draft" | "submitted" | "in_review" | "decided";
    award_status: "awarded" | "denied" | "revised" | "withdrawn";
    rationale: string | null;
    updated_at: string; // ISO 8601
  }[];
}

type AidBucket = "need" | "mission" | "marketing" | "merit" | "hardship";
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
- Adding new enum values
- Changing error message text
- Adjusting default pagination limit (within bounds)

---

## Testing This Contract

### Via curl

```bash
# Summary
curl -i \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-Id: $SCHOOL_ID" \
  https://crown-api-dev.azurewebsites.net/api/v1/financial-aid/summary/

# Drilldown with pagination
curl -i \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-Id: $SCHOOL_ID" \
  "https://crown-api-dev.azurewebsites.net/api/v1/financial-aid/drilldown/?bucket=need&limit=25&offset=0"
```

### Via PowerShell

```powershell
$API = "https://crown-api-dev.azurewebsites.net"
$token = (Invoke-RestMethod -Uri "$API/api/v1/auth/token/" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{username="head@crown-demo.local"; password="Joanne1023$"} | ConvertTo-Json -Compress)).access

$schoolId = "e5e7bec0-7e8a-4c8a-9b5c-7e8a4c8a9b5c"

# Summary
$summary = Invoke-RestMethod -Uri "$API/api/v1/financial-aid/summary/" `
  -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$schoolId}

# Drilldown
$drilldown = Invoke-RestMethod -Uri "$API/api/v1/financial-aid/drilldown/?bucket=need&limit=25&offset=0" `
  -Headers @{"Authorization"="Bearer $token"; "X-School-Id"=$schoolId}
```

---

## Contract Tests

This contract is **automatically enforced** by:  
**`backend/financial_aid/tests/test_financial_aid_endpoints.py`**

- **11 automated tests** validate every response shape, field type, and status code
- Tests fail if actual API behavior drifts from frozen contract
- Run locally: `python backend/manage.py test financial_aid.tests.test_financial_aid_endpoints`

**Example Test (Invalid Bucket → 400):**
```python
def test_drilldown_invalid_bucket_400(self):
    url = reverse("financial_aid:drilldown") + "?bucket=INVALID"
    response = self.client.get(url, HTTP_X_SCHOOL_ID=str(self.school.id))
    self.assertEqual(response.status_code, 400)
    self.assertIn("bucket", response.json()["error"].lower())
```

These tests prevent "but the doc says..." bugs by ensuring the contract is **enforced in code**.

---

## Support

- **Issues:** See [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md)
- **Changes:** Coordinate with @tcmegahan before breaking edits
- **Smoke Tests:** Run `test_azure_smoke.ps1` post-deployment

