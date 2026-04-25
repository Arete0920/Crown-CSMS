# DIRECTOR FRAMEWORK CONTRACT

**Version:** 1.0
**Date:** 2026-01-04
**Architecture:** Unified Dashboard (Multi-Persona)

---

## Pattern: Unified Director Dashboard

Crown 2026 uses a **unified dashboard** approach where all director personas (Aid, Admissions, Finance, Registrar) share:
- One HTML page
- One set of API endpoints
- One JavaScript-powered UI

This is intentionally **NOT persona-specific routes** (e.g., separate `/director/admissions/` pages).

### Why Unified?

**Advantages:**
- ✅ Consistent UX across all director roles
- ✅ Single source of truth for director workflows
- ✅ Easier maintenance (fix once, applies everywhere)
- ✅ Supports multi-role users (Head of School sees everything)
- ✅ Reduces code duplication

**Trade-offs:**
- ⚠️ Tighter coupling between director modules
- ⚠️ All director data loads at once (acceptable at current scale)

---

## Framework Contract

### 1. Page Route

**Single shared page:**
```
/director/
```

**Template:** `crown_api/templates/director_dashboard.html`

**Requirements:**
- Must be JavaScript-powered (fetches data from APIs)
- Must support persona-based UI filtering (future enhancement)
- Must handle authentication (only director roles allowed)

---

### 2. API Routes

All director APIs live under `/api/director/*` namespace:

```
/api/director/dashboard/      → Summary metrics for all personas
/api/director/priority/        → Unified priority queue (worklist)
/api/director/timeline/        → Timeline events
/api/director/actions/         → Action handlers (POST)
/api/director/<persona>/summary/ → Persona-specific detailed metrics
```

**Location:** `crown_api/api_urls.py`

---

### 3. Priority Queue API Contract

**Endpoint:** `GET /api/director/priority/`

**Response Shape (MUST MATCH):**

```json
{
  "meta": {
    "school_id": "<uuid>",
    "year_id": "<uuid>"
  },
  "worklist_top_10": [
    {
      "type": "AID_APPLICATION_NEEDS_INFO",
      "score": 107,
      "id": "<uuid>",
      "family": "Smith",
      "submitted_at": "2026-01-01T10:00:00Z",
      "summary": "Application needs info (missing documents)."
    }
  ],
  "aid": {
    "needs_info_applications": [...],
    "under_review_applications": [...],
    "accepted_not_posted_awards": [...]
  },
  "admissions": {
    "needs_info_applications": [...],
    "under_review_applications": [...]
  },
  "finance": {
    "top_balances_due": [...],
    "students_billed_count": 0
  },
  "registrar": {
    "enrollments_missing_grade_count": 0
  }
}
```

**Rules:**
- ✅ `worklist_top_10` is a **merged** array sorted by `score` descending
- ✅ Each persona section contains raw query results (not scored)
- ✅ Item types follow pattern: `<PERSONA>_<ENTITY>_<STATUS>`
  - Examples: `AID_APPLICATION_NEEDS_INFO`, `ADMISSIONS_APPLICATION_UNDER_REVIEW`, `FINANCE_BALANCE_DUE`
- ✅ All timestamps use ISO 8601 format
- ✅ All IDs are strings (even if UUIDs)

---

### 4. Dashboard API Contract

**Endpoint:** `GET /api/director/dashboard/`

**Response Shape:**

```json
{
  "meta": {
    "school_id": "<uuid>",
    "year_id": "<uuid>",
    "user_roles": ["ROLE_AID_DIRECTOR"]
  },
  "aid": {
    "applications_count": 63,
    "under_review_count": 12,
    "needs_info_count": 5
  },
  "admissions": {
    "applications_count": 0,
    "under_review_count": 0,
    "needs_info_count": 0
  },
  "finance": {
    "total_billed_cents": 150000000,
    "total_received_cents": 120000000
  },
  "registrar": {
    "total_enrollments": 250
  }
}
```

**Rules:**
- ✅ High-level counts/aggregates only (not full records)
- ✅ Each persona section follows same structure as priority API
- ✅ Must be fast (<500ms response time)

---

### 5. Timeline API Contract

**Endpoint:** `GET /api/director/timeline/`

**Response Shape:**

```json
{
  "events": [
    {
      "timestamp": "2026-01-04T10:30:00Z",
      "type": "AID_APPLICATION_SUBMITTED",
      "actor": "john.doe@example.com",
      "summary": "Application submitted by Smith family",
      "id": "<uuid>"
    }
  ]
}
```

**Rules:**
- ✅ Events sorted by `timestamp` descending (newest first)
- ✅ Limit to last 50 events
- ✅ Event types follow pattern: `<PERSONA>_<ENTITY>_<ACTION>`

---

### 6. Actions API Contract

**Endpoint:** `POST /api/director/actions/`

**Request Body:**

```json
{
  "action": "POST_ACCEPTED_AWARDS",
  "payload": {
    "award_ids": ["<uuid>", "<uuid>"]
  }
}
```

**Response Shape:**

```json
{
  "success": true,
  "message": "Posted 2 awards to ledger",
  "affected_count": 2
}
```

**Rules:**
- ✅ Action names follow pattern: `<VERB>_<ENTITY>_<PLURAL>`
  - Examples: `POST_ACCEPTED_AWARDS`, `APPROVE_APPLICATIONS`, `SEND_DECISIONS`
- ✅ Must be idempotent (safe to retry)
- ✅ Must return affected count for audit

---

## Adding a New Director Module

To add a new director module (e.g., Registrar, Athletics), follow this checklist:

### Step 1: Create Models (Clone Aid Pattern)

**File:** `backend/<module>/models.py`

1. Clone `aid/models.py` → `<module>/models.py`
2. Keep these patterns:
   - `STATUS_*` constants
   - Foreign keys: `school`, `academic_year`, `family`, `student`
   - Timestamps: `created_at`, `updated_at`
   - Related models: `*Review`, `*Decision`, `*AuditEvent`

**Commit:** `git commit -m "Create <module> models (clone from Aid)"`

### Step 2: Integrate into director_views.py

**File:** `backend/crown_api/director_views.py`

#### 2.1 Add Import
```python
from <module>.models import <Module>Application
```

#### 2.2 Add Priority Queries

Clone from Aid pattern (around line 428-470):

```python
# --- <Module> priorities (cloned from Aid) ---
<module>_needs_info_apps = (
    <Module>Application.objects
    .filter(school_id=school_id, academic_year=academic_year,
            status=<Module>Application.STATUS_NEEDS_INFO)
    .select_related("family")
    .order_by("-submitted_at")[:10]
)
```

#### 2.3 Add Scoring Logic

Clone from Aid pattern (around line 497-543):

```python
# Build scored items (<Module>)
<module>_items = []
for a in <module>_needs_info_apps:
    score = 100 + (days_waiting(a.submitted_at) * 3)  # Same urgency
    <module>_items.append({
        "type": "<MODULE>_APPLICATION_NEEDS_INFO",
        "score": score,
        "id": str(a.id),
        "family": getattr(a.family, "family_name", None),
        "submitted_at": a.submitted_at,
        "summary": f"{<module>} application needs info (missing documents).",
    })
```

#### 2.4 Update Worklist Merge

```python
worklist = sorted(
    aid_items + admissions_items + <module>_items + finance_items + registrar_items,
    key=lambda x: x["score"],
    reverse=True
)[:10]
```

#### 2.5 Add to API Response

```python
"<module>": {
    "needs_info_applications": [...],
    "under_review_applications": [...]
},
```

**Commit:** `git commit -m "Add <module> to unified director priority queue"`

### Step 3: Test

```python
# Create test script
python test_<module>_api.py

# Expected output:
# ✅ API call successful!
# ✅ <Module> section present in response!
```

### Step 4: Tag as Anchor

If all tests pass:

```bash
git tag anchor-<module>-director-v1
git push origin anchor-<module>-director-v1
```

---

## Validation Checklist

Before tagging a new director module as an anchor:

### API Tests (curl/Invoke-RestMethod)

```powershell
# 1. Priority queue includes module section
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/director/priority/" | ConvertTo-Json -Depth 3

# Expected: Contains "<module>" key with needs_info_applications, under_review_applications

# 2. Worklist merges items correctly
# Expected: worklist_top_10 contains items with type "<MODULE>_*"

# 3. Dashboard includes module metrics
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/director/dashboard/" | ConvertTo-Json -Depth 3

# Expected: Contains "<module>" key with counts
```

### Browser Tests

1. ✅ Visit `http://127.0.0.1:8000/director/` → Dashboard loads
2. ✅ Priority queue table shows mixed items (Aid, Admissions, Finance, etc.)
3. ✅ KPI cards show metrics for all personas
4. ✅ No console errors in browser dev tools

### Code Quality

1. ✅ `python manage.py check` → No issues
2. ✅ Item types follow naming convention: `<PERSONA>_<ENTITY>_<STATUS>`
3. ✅ Scoring formula matches Aid pattern (100+ for urgent, 60+ for moderate)
4. ✅ Response shape matches contract (same keys as other personas)

---

## Current Anchors

### anchor-financial-aid-director-v1
**Date:** 2026-01-03
**Commit:** af946be
**Status:** ✅ Gold Standard

**What's included:**
- Aid models (AidApplication, AidAward, AidDocument, etc.)
- Priority queries (needs_info, under_review, accepted_not_posted)
- Scoring logic (100+ for needs_info, 90+ for accepted awards, 60+ for under_review)
- API integration (aid section in priority queue)

### anchor-admissions-director-v1
**Date:** 2026-01-04
**Commit:** e337b3a
**Status:** ✅ Validated

**What's included:**
- Admissions models (AdmissionsApplication, AdmissionsReview, etc.)
- Priority queries (needs_info, under_review)
- Scoring logic (cloned from Aid: 100+ for needs_info, 60+ for under_review)
- API integration (admissions section in priority queue)

**Validation results:**
```json
{
  "admissions": {
    "needs_info_applications": [],
    "under_review_applications": []
  }
}
```

---

## Implementation Location

```
backend/
├── crown_api/
│   ├── director_views.py          ← Core framework implementation
│   ├── api_urls.py                ← API route definitions
│   ├── urls.py                    ← Page route definition
│   ├── templates/
│   │   └── director_dashboard.html ← Shared UI template
│   └── views.py                    ← Page rendering
├── aid/
│   └── models.py                   ← Gold standard models
├── admissions/
│   └── models.py                   ← Cloned from Aid
└── finance/
    └── models.py                   ← Finance-specific models
```

---

## Response Time Targets

All API endpoints must meet these targets:

- `/api/director/priority/` → <1000ms (complex query with joins)
- `/api/director/dashboard/` → <500ms (counts only)
- `/api/director/timeline/` → <800ms (50 events with joins)
- `/api/director/actions/` → <2000ms (includes database writes)

**Optimization strategies:**
- Use `.select_related()` for foreign key joins
- Limit query results (e.g., `[:10]` for worklist, `[:50]` for timeline)
- Add database indexes on frequently filtered fields (school_id, academic_year, status)

---

## Authentication & Authorization

**Required roles:**
- `ROLE_AID_DIRECTOR`
- `ROLE_ADMISSIONS_DIRECTOR`
- `ROLE_FINANCE_DIRECTOR`
- `ROLE_REGISTRAR`
- `ROLE_HEAD_OF_SCHOOL` (sees everything)

**Implementation:** `crown_director_allowed(request)` function in `director_views.py`

**Rules:**
- ✅ All `/director/` routes require authentication
- ✅ All `/api/director/*` endpoints require authentication
- ✅ Persona-specific filtering is optional (current: all directors see all data)
- ✅ Future enhancement: Filter worklist by user's role

---

## Version History

### v1.0 (2026-01-04)
- Initial framework definition
- Unified dashboard pattern established
- Aid and Admissions modules validated
- Contract documented

---

**Maintained by:** Crown 2026 Team
**Questions?** See `director_views.py` or `REFERENCE_MODULE_PATTERN.md`
