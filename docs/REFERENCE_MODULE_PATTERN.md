# REFERENCE MODULE PATTERN

**Last Updated:** 2026-01-04
**Gold Standard:** Financial Aid Director
**Clone Target:** Admissions Director

## Philosophy: Copy-Paste-Modify, Not Recreate

When adding a new director module to Crown 2026, **CLONE the working Aid pattern** rather than recreating from scratch. This prevents "divergence debt" where implementations drift apart over time.

---

## Step-by-Step Cloning Process

### Phase 1: Create Models (70-80% Similar to Aid)

**Location:** `backend/[module]/models.py`

1. Clone `aid/models.py` → `admissions/models.py`
2. Find-replace field names:
   - `AidApplication` → `AdmissionsApplication`
   - Aid-specific fields (e.g., `requested_amount_cents`) → Module-specific fields (e.g., `gpa`, `test_score`)
3. Keep shared patterns:
   - `STATUS_*` constants (DRAFT, SUBMITTED, UNDER_REVIEW, NEEDS_INFO, etc.)
   - Foreign keys: `school`, `academic_year`, `family`, `student`
   - Audit timestamps: `created_at`, `updated_at`, `created_by`, `updated_by`
   - Related models: `*Review`, `*Decision`, `*AuditEvent`

**Commit:** `git commit -m "Create admissions models (clone from Aid pattern)"`

---

### Phase 2: Integrate into Unified Director APIs

**DO NOT** create separate `admissions/views.py` with its own dashboard.
**DO** augment the existing unified director APIs in `crown_api/director_views.py`.

#### 2.1 Add Import

```python
# Line 12 (after Aid import)
from aid.models import AidApplication, AidAward, AidDocument
from admissions.models import AdmissionsApplication  # ← ADD THIS
```

#### 2.2 Clone Priority Queries

Find the Aid priority queries (around line 428-454) and clone them:

```python
# --- Aid priorities ---
needs_info_apps = (
    AidApplication.objects
    .filter(school_id=school_id, academic_year=academic_year, status=AidApplication.STATUS_NEEDS_INFO)
    .select_related("family")
    .order_by("-submitted_at")[:10]
)

# --- Admissions priorities (CLONED FROM AID) ---
admissions_needs_info_apps = (
    AdmissionsApplication.objects
    .filter(school_id=school_id, academic_year=academic_year, status=AdmissionsApplication.STATUS_NEEDS_INFO)
    .select_related("family")
    .order_by("-submitted_at")[:10]
)
```

**Pattern to clone:**
- `.filter(school_id, academic_year, status)`
- `.select_related("family")` for joins
- `.order_by("-submitted_at")` for descending sort
- `[:10]` to limit results

#### 2.3 Clone Scoring Logic

Find where `aid_items = []` is built (around line 497-543) and clone:

```python
# Build scored items (Aid)
aid_items = []
for a in needs_info_apps:
    score = 100 + (days_waiting(a.submitted_at) * 3)
    aid_items.append({
        "type": "AID_APPLICATION_NEEDS_INFO",
        "score": score,
        "id": str(a.id),
        "family": getattr(a.family, "family_name", None),
        "submitted_at": a.submitted_at,
        "summary": "Application needs info (missing documents).",
    })

# Build scored items (Admissions - CLONED FROM AID)
admissions_items = []
for a in admissions_needs_info_apps:
    score = 100 + (days_waiting(a.submitted_at) * 3)  # Same urgency scoring
    admissions_items.append({
        "type": "ADMISSIONS_APPLICATION_NEEDS_INFO",  # ← Change type prefix
        "score": score,
        "id": str(a.id),
        "family": getattr(a.family, "family_name", None),
        "submitted_at": a.submitted_at,
        "summary": "Admissions application needs info (missing documents).",  # ← Update summary
    })
```

**Scoring formula (clone from Aid):**
- `needs_info`: `100 + (days_waiting * 3)` (urgent - missing docs)
- `under_review`: `60 + (days_waiting * 2)` (moderate urgency)

#### 2.4 Update Worklist Merge

Find the `worklist = sorted(...)` line (around line 573) and add `admissions_items`:

```python
# OLD
worklist = sorted(
    aid_items + finance_items + registrar_items,
    key=lambda x: x["score"],
    reverse=True
)[:10]

# NEW
worklist = sorted(
    aid_items + admissions_items + finance_items + registrar_items,  # ← ADD admissions_items
    key=lambda x: x["score"],
    reverse=True
)[:10]
```

#### 2.5 Add to API Response Payload

Find the `return Response({...})` in `director_priority` (around line 606) and add admissions section after aid:

```python
return Response({
    "meta": {...},
    "worklist_top_10": worklist,
    "aid": {
        "needs_info_applications": [...],
        "under_review_applications": [...],
    },
    "admissions": {  # ← ADD THIS SECTION
        "needs_info_applications": [
            {
                "application_id": str(a.id),
                "family": getattr(a.family, "family_name", None),
                "submitted_at": a.submitted_at,
            }
            for a in admissions_needs_info_apps
        ],
        "under_review_applications": [
            {
                "application_id": str(a.id),
                "family": getattr(a.family, "family_name", None),
                "submitted_at": a.submitted_at,
            }
            for a in admissions_under_review_apps
        ],
    },
    "finance": {...},
    "registrar": {...}
})
```

**Commit:** `git commit -m "Add admissions to unified director priority queue"`

---

### Phase 3: Wire Persona-Based Routing (Future)

**Current state:** Unified dashboard shows all director types in one worklist.

**Future enhancement:** Route by `UserRole`:
- Aid Director → sees Aid priorities first
- Admissions Director → sees Admissions priorities first
- Head of School → sees all priorities

**Implementation location:** `crown_api/views.py` in `director_dashboard_page` function.

---

## Testing Checklist

After cloning:

1. **Django check:** `python manage.py check` → ✅ No issues
2. **API test:** Run `test_admissions_api.py`:
   ```
   ✅ Admissions section present in response
   ✅ worklist_top_10 includes admissions items (if data exists)
   ```
3. **Browser test:** Visit `http://127.0.0.1:8000/director/`
   - JavaScript should fetch `/api/director/priority/`
   - Admissions items should appear in priority queue table

---

## Anti-Patterns to Avoid

❌ **DON'T** create `admissions/views.py` with separate dashboard
❌ **DON'T** create `admissions/templates/admissions/dashboard.html`
❌ **DON'T** add `path('admissions/', ...)` to URLs

✅ **DO** use the shared `director_dashboard.html` template
✅ **DO** augment the unified `/api/director/*` endpoints
✅ **DO** follow the exact Aid scoring pattern

---

## Why This Approach?

### Benefits
- **Consistency:** All directors use same UI/UX
- **Maintainability:** Fix once, applies to all directors
- **No divergence:** Code stays synchronized
- **Fast:** Clone working code in ~30 minutes vs. 4+ hours recreation

### Trade-offs
- **Tight coupling:** Modules share API endpoints (acceptable for director workflows)
- **Monolithic:** All director logic in one file (manageable at current scale)

---

## File Locations

```
backend/
├── crown_api/
│   ├── director_views.py          ← GOLD STANDARD (unified director APIs)
│   ├── templates/
│   │   └── director_dashboard.html ← Shared template (JavaScript-powered)
│   └── views.py                    ← Persona routing (future)
├── aid/
│   └── models.py                   ← Gold standard models
└── admissions/
    └── models.py                   ← Cloned from Aid (70-80% similar)
```

---

## Git Tags

- **anchor-financial-aid-director-v1** → Gold standard reference point
- Use `git diff anchor-financial-aid-director-v1 HEAD -- backend/crown_api/director_views.py` to see what changed

---

## Next Module: Registrar

When adding Registrar director:
1. Clone enrollment models from `core/models.py` (Enrollment already exists)
2. Add `registrar_items` to `director_priority` function (already partially done)
3. Add `registrar` section to API response
4. Update `worklist = sorted(aid_items + admissions_items + registrar_items + finance_items, ...)`

---

**Maintained by:** Crown 2026 Team
**Questions?** See `director_views.py` lines 413-660 for complete implementation.
