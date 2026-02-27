# Crown2026 — Dashboards & Reporting Module: Phase A Specification

**Date**: 2026-02-25  
**Branch**: `feature/phase-10-dashboards-module`  
**PR**: [#442](https://github.com/tcmegahan/Crown2026/pull/442)  
**Status**: Committed. 25/25 contract tests pass. All 6 roles smoke-verified.

---

## 1. Architecture Map (exact repo paths)

```
Crown2026/
├── backend/
│   └── crown_api/
│       └── dashboards/
│           ├── tenant.py          ← get_dashboard_school_id() — tenant enforcement
│           ├── serializers.py     ← DRF contract serializers for all 4 endpoints
│           ├── summary.py         ← Role-based widget builder service
│           ├── views.py           ← Me / Summary / Drilldown / Alerts views
│           ├── urls.py            ← URL registration (wired into api_v1_urls.py)
│           ├── academics.py       ← Legacy: EnrollmentSnapshotView (keep, read-only)
│           ├── admissions.py      ← Legacy: AdmissionsFunnelView (keep, read-only)
│           └── finance.py         ← Legacy: FinanceSummaryView (keep, read-only)
│   └── tests/
│       └── test_dashboards_role_contract.py  ← 25 contract tests
│
├── frontend/
│   └── dashboards/
│       └── src/
│           ├── api/
│           │   └── dashboards.js        ← fetchDashboardMe/Summary/Drilldown/Alerts
│           ├── lib/
│           │   └── http.js              ← httpJson() — never throws, returns {ok,status,data,error}
│           ├── components/
│           │   ├── crown/
│           │   │   ├── CrownLayout.jsx  ← Page shell (title, subtitle, right slot)
│           │   │   ├── CrownCard.jsx    ← Base card primitive
│           │   │   ├── CrownMetricCard.jsx
│           │   │   └── CrownGrid.jsx
│           │   └── dashboard/
│           │       ├── WidgetDispatcher.jsx   ← switch(type) → component
│           │       ├── StatWidget.jsx         ← KPI tile
│           │       ├── FlipWidget.jsx         ← CSS 3D flip (front/back)
│           │       ├── TableWidget.jsx        ← Data table
│           │       ├── QuickActionsWidget.jsx ← Action/link grid
│           │       ├── FeedWidget.jsx         ← Thread/event list
│           │       ├── ChartWidget.jsx        ← SVG donut + sparkline
│           │       └── DrilldownDrawer.jsx    ← Slide-in panel (aria-modal)
│           ├── pages/
│           │   └── RoleDashboardPage.jsx  ← /dash/:role — unified role page
│           └── routes/
│               └── router.jsx             ← React Router v6 (added /dash/:role)
│
└── frontend/dashboards/tests/ui/
    └── dashboard-smoke.spec.ts            ← Playwright 6-role smoke test
```

---

## 2. URL Registration (how endpoints reach the internet)

### Backend URL chain (do not break these includes)

```python
# backend/crown_api/urls.py (top-level Django urls.conf)
path("api/v1/", include("crown_api.api_v1_urls"))   # namespace: api/v1/
path("api/",    include("crown_api.api_v1_urls"))    # legacy alias

# backend/crown_api/api_v1_urls.py
path("", include("crown_api.api_urls"))              # mounts api_urls

# backend/crown_api/api_urls.py
path("", include("crown_api.dashboards.urls"))       # mounts dashboard paths
```

### Effective live URLs (both paths resolve)

| Name | Path (under /api/v1/ and /api/) |
|------|---------------------------------|
| `dashboard_me` | `GET /api/dashboards/me/` |
| `dashboard_summary` | `GET /api/dashboards/summary/` |
| `dashboard_drilldown` | `GET /api/dashboards/drilldown/?widget=<key>` |
| `dashboard_alerts` | `GET /api/dashboards/alerts/` |
| `dashboard_admissions_funnel` | `GET /api/dashboards/admissions/funnel/` (legacy) |
| `dashboard_finance_summary` | `GET /api/dashboards/finance/summary/` (legacy) |
| `dashboard_academics_enrollment` | `GET /api/dashboards/academics/enrollment/` (legacy) |

---

## 3. Tenant Header Enforcement (exact wiring)

### Header constants (from `backend/households/scoping.py`)

```python
CANONICAL_SCHOOL_HEADER = "X-School-Id"      # primary header
LEGACY_SCHOOL_HEADER    = "X-Crown-School-Id" # backward-compat alias
```

### Tenant resolver (`backend/crown_api/dashboards/tenant.py`)

```python
from households.scoping import CANONICAL_SCHOOL_HEADER, LEGACY_SCHOOL_HEADER

def get_dashboard_school_id(request, *, required: bool = True) -> uuid.UUID | None:
    raw = (
        request.headers.get(CANONICAL_SCHOOL_HEADER) or
        request.headers.get(LEGACY_SCHOOL_HEADER)
    )
    if not raw:
        if required:
            raise ValidationError({"school_id": [f"Missing {CANONICAL_SCHOOL_HEADER} header"]})
        return None

    try:
        sid = uuid.UUID(str(raw))
    except (TypeError, ValueError):
        raise ValidationError({"school_id": ["Invalid school_id UUID."]})

    # Cross-tenant block: non-staff user must match header school
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        if not (user.is_staff or user.is_superuser):
            user_sid = getattr(user, "school_id", None) or getattr(getattr(user, "school", None), "id", None)
            if not user_sid:
                raise ValidationError({"school_id": ["User missing school context."]})
            if str(user_sid) != str(sid):
                raise NotFound({"detail": "Not found"})

    # School must exist in DB
    if not School.objects.filter(id=sid).exists():
        raise NotFound({"detail": "School not found"})

    return sid
```

### Response codes

| Condition | HTTP |
|-----------|------|
| No header | 400 |
| Malformed UUID | 400 |
| Header school ≠ user school (non-staff) | 404 |
| School UUID not in DB | 404 |
| Valid + authorized | 200 (continues) |

---

## 4. RBAC Wiring (exact implementation)

### Location: `backend/crown_api/dashboards/views.py`

```python
_VALID_ROLES = frozenset({
    "admin", "teacher", "parent", "student",
    "finance", "registrar", "staff", "board",
})

def _resolve_role(request) -> str:
    # 1. Try request.user.role (real production path)
    user_role = getattr(request.user, "role", None)
    if user_role and str(user_role).strip().lower() in _VALID_ROLES:
        return str(user_role).strip().lower()

    # 2. X-Demo-Role header — ONLY when ALLOW_DEMO_ROLE_HEADER=1 (dev/CI)
    if os.getenv("ALLOW_DEMO_ROLE_HEADER") == "1":
        hdr = request.headers.get("X-Demo-Role") or request.META.get("HTTP_X_DEMO_ROLE")
        if hdr and str(hdr).strip().lower() in _VALID_ROLES:
            return str(hdr).strip().lower()

    return "admin"  # safe default
```

### How to set up in dev/CI

```bash
# .env or environment
ALLOW_DEMO_ROLE_HEADER=1   # enables X-Demo-Role header fallback
```

---

## 5. API Contracts (all 4 endpoints)

### 5.1 `GET /api/dashboards/me/`

**Request headers**

```
X-School-Id: <uuid>
Authorization: Bearer <jwt>
```

**Response 200**

```json
{
  "school_id": "19801b59-8c05-4c84-9312-5d792e4e839d",
  "display_name": "Principal Johnson",
  "roles": ["admin"],
  "default_route": "/dash/admin",
  "features": {
    "flip_cards": true,
    "drilldowns": true
  }
}
```

**Serializer**: `DashboardMeSerializer` in `backend/crown_api/dashboards/serializers.py`

---

### 5.2 `GET /api/dashboards/summary/`

**Request headers**: same as above

**Response 200**

```json
{
  "role": "admin",
  "school_id": "19801b59-8c05-4c84-9312-5d792e4e839d",
  "generated_at": "2026-02-25T21:00:00+00:00",
  "widgets": [
    {
      "key": "quick_actions",
      "type": "actions",
      "title": "Quick Actions",
      "subtitle": "",
      "size": "md",
      "priority": 10,
      "data": {
        "actions": [
          { "label": "Message a family", "to": "/comms/compose" },
          { "label": "View unpaid balances", "to": "/finance" }
        ]
      },
      "drilldown": { "enabled": false, "endpoint": "/api/dashboards/drilldown/?widget=quick_actions" }
    },
    {
      "key": "alerts_flip",
      "type": "flip",
      "title": "School Health",
      "subtitle": "Tap to see action items",
      "size": "md",
      "priority": 20,
      "data": {
        "front": { "good": 12, "warn": 4, "bad": 1 },
        "back": {
          "items": [
            { "level": "warn", "text": "2 students trending toward chronic absenteeism" },
            { "level": "bad",  "text": "1 payment past due > 30 days" },
            { "level": "warn", "text": "3 missing grade submissions" }
          ]
        }
      },
      "drilldown": { "enabled": true, "endpoint": "/api/dashboards/drilldown/?widget=alerts_flip" }
    }
  ]
}
```

**Serializer**: `DashboardSummarySerializer` → `DashboardWidgetSerializer`

---

### 5.3 `GET /api/dashboards/drilldown/?widget=<key>`

**Response 200**

```json
{
  "widget": "alerts_flip",
  "school_id": "19801b59-...",
  "page": 1,
  "has_more": false,
  "rows": [
    { "label": "Chronic absenteeism", "value": 2, "action": "/teacher/attendance" }
  ]
}
```

> Phase A: returns stub rows with `"coming": "Phase B"` shape.  
> Phase B: replace `DashboardDrilldownView.get()` with real paginated ORM queries per widget key.

---

### 5.4 `GET /api/dashboards/alerts/`

**Response 200**

```json
{
  "school_id": "19801b59-...",
  "generated_at": "2026-02-25T21:00:00+00:00",
  "alerts": [
    {
      "key": "alert_missing_grades",
      "level": "warn",
      "text": "3 teachers have ungraded submissions older than 7 days",
      "action_url": "/academics",
      "widget": "alerts_flip"
    }
  ]
}
```

**Serializer**: `DashboardAlertsResponseSerializer` → `DashboardAlertSerializer`

---

## 6. Widget Registry (stable — never rename keys after shipping)

| Key | Type | Title | Roles | Size | Priority | Phase A Data |
|-----|------|-------|-------|------|----------|--------------|
| `quick_actions` | `actions` | Quick Actions | all | `md` | 10 | Role-specific links from `_quick_actions()` |
| `alerts_flip` | `flip` | School Health | all | `md` | 20 | Stub counts; Phase B: real queries |
| `enrollment_snapshot` | `stat` | Total Enrollment | admin, registrar | `sm` | 30 | Live: `Student.objects.filter(school_id=..., is_active=True).count()` |
| `sections_count` | `stat` | Active Sections | admin, registrar, teacher | `sm` | 35 | Live: `Section.objects.filter(school_id=...).count()` |
| `attendance_risk` | `chart_donut` | Attendance Risk | admin, registrar, teacher | `md` | 40 | Stub: `{"at_risk": 14, "total": 210}` |
| `missing_work` | `table` | Missing Work | teacher, student | `md` | 50 | Stub table rows |
| `grades_trend` | `chart_line` | Grade Trend | parent, student | `md` | 40 | Stub sparkline data |
| `balances` | `stat` | Family Balance | parent, finance | `sm` | 30 | Stub; Phase B: household billing model |
| `payments_this_month` | `stat` | Payments This Month | finance | `sm` | 35 | Stub; Phase B: finance models |
| `messages_inbox` | `feed` | Messages | all | `sm` | 900 | Stub thread list |
| `events_upcoming` | `feed` | Upcoming Events | all | `sm` | 910 | Stub event list |

### Widget counts per role

| Role | Widgets | Keys |
|------|---------|------|
| admin | 7 | quick_actions, alerts_flip, enrollment_snapshot, sections_count, attendance_risk, messages_inbox, events_upcoming |
| teacher | 7 | quick_actions, alerts_flip, sections_count, attendance_risk, missing_work, messages_inbox, (varies) |
| parent | 6 | quick_actions, alerts_flip, grades_trend, balances, messages_inbox, events_upcoming |
| student | 6 | quick_actions, alerts_flip, missing_work, grades_trend, messages_inbox, events_upcoming |
| finance | 6 | quick_actions, alerts_flip, balances, payments_this_month, messages_inbox, events_upcoming |
| registrar | 7 | quick_actions, alerts_flip, enrollment_snapshot, sections_count, attendance_risk, messages_inbox, events_upcoming |

---

## 7. Widget Type → Component Map (frontend)

### File: `frontend/dashboards/src/components/dashboard/WidgetDispatcher.jsx`

```jsx
switch (widget.type) {
  case "stat":       → StatWidget.jsx
  case "flip":       → FlipWidget.jsx
  case "table":      → TableWidget.jsx
  case "actions":    → QuickActionsWidget.jsx
  case "feed":       → FeedWidget.jsx
  case "chart_line":
  case "chart_donut":→ ChartWidget.jsx   // SVG-only, no recharts dep
}
```

### Component → data shape contract

**StatWidget** (`type: "stat"`)
```json
{ "count": 247, "label": "Active students", "status": "good|warn|bad|due_soon", "amount": 12450.00 }
```
Renders: `data.count ?? data.amount ?? data.total` with Intl currency formatting when `data.amount` present.

**FlipWidget** (`type: "flip"`)
```json
{
  "front": { "good": 12, "warn": 4, "bad": 1 },
  "back": {
    "items": [{ "level": "warn|bad|good", "text": "..." }]
  }
}
```
CSS-only 3D flip, no framer-motion. Accessible: each face has `aria-hidden` when not active.

**TableWidget** (`type: "table"`)
```json
{ "columns": ["Col A", "Col B", "Count"], "rows": [["Value", "Value", 3]] }
```
Number cells render as red badge. Empty state: "No data to display."

**QuickActionsWidget** (`type: "actions"`)
```json
{ "actions": [{ "label": "Take attendance", "to": "/teacher/attendance" }] }
```
CSS grid of `<a>` links. Gold hover accent via CSS class.

**FeedWidget** (`type: "feed"`)
```json
{
  "threads": [{ "from": "Parent", "subject": "Question", "ago": "2h" }],
  "events":  [{ "name": "Graduation", "date": "Mar 15" }]
}
```
Adapts `data.threads ?? data.events ?? data.items`.

**ChartWidget** (`type: "chart_donut"` or `"chart_line"`)
```json
// donut:
{ "at_risk": 14, "total": 210 }

// sparkline:
{ "points": [81, 85, 78, 82, 88], "labels": ["Sep", "Oct", "Nov", "Dec", "Jan"] }
```
Pure SVG — arc path via `Math.cos`/`Math.sin`. No recharts. No external dependency.

---

## 8. Frontend Session Storage Keys

All dashboard API calls read from `sessionStorage`:

| Key | Purpose | Set by |
|-----|---------|--------|
| `crown.jwt.access` | Bearer token for `Authorization` header | LoginPage on session start |
| `crown.school.id` | `X-School-Id` header value (UUID string) | LoginPage on session start |
| `crown.role` | Display role (not used for auth decisions) | LoginPage or RoleHomeRedirect |

### API client header builder (`frontend/dashboards/src/api/dashboards.js`)

```javascript
function _headers(schoolId, role) {
  const h = { "Accept": "application/json", "Content-Type": "application/json" };
  const sid = schoolId || sessionStorage.getItem("crown.school.id");
  const tok = sessionStorage.getItem("crown.jwt.access");
  if (sid) h["X-School-Id"] = sid;
  if (tok) h["Authorization"] = `Bearer ${tok}`;
  if (role) h["X-Demo-Role"] = role;  // only active if ALLOW_DEMO_ROLE_HEADER=1
  return h;
}
```

---

## 9. Frontend Route

### File: `frontend/dashboards/src/routes/router.jsx`

```jsx
{
  path: '/dash/:role',
  element: <RoleDashboardPage />,
}
```

**Role values** accepted by the route param: `admin`, `teacher`, `parent`, `student`, `finance`, `registrar`, `board`, `staff` (and any future addition to `_VALID_ROLES` in `views.py`).

**Existing per-role legacy routes** that still work:

| Legacy path | Component |
|-------------|-----------|
| `/teacher` | `TeacherDashboard.jsx` |
| `/parent`  | `ParentDashboard.jsx` |
| `/student` | `StudentDashboard.jsx` |
| `/admin` (varies) | `AdminDashboard.jsx` |
| ...30+ others | (see `router.jsx` lines 60–270) |

`/dash/:role` is the **new unified path**. Legacy routes remain for backward compatibility.

---

## 10. RoleDashboardPage Logic Map

**File**: `frontend/dashboards/src/pages/RoleDashboardPage.jsx`

```
mount (role, schoolId from params + sessionStorage)
  └── fetchDashboardSummary(schoolId, role)
        ├── ok → sort widgets by priority → render grid
        └── error → show error banner (role="alert")

loading state → 4× WidgetSkeleton (shimmer animation via crown-shimmer keyframe)

grid → 12-column CSS grid
  └── each widget:
        ├── gridColumn = SIZE_COLS[widget.size]   (sm→span4, md→span6, lg→span12)
        └── WidgetDispatcher(widget, onExpand)
              └── if widget.drilldown.enabled: onExpand opens DrilldownDrawer
```

**Key data attributes** for Playwright targeting:

```jsx
<div data-testid="dashboard-grid">
  <div data-widget-key={w.key} />   // e.g., data-widget-key="enrollment_snapshot"
</div>
```

---

## 11. Playwright Test Patterns

### File: `frontend/dashboards/tests/ui/dashboard-smoke.spec.ts`

### Session seeding (matches existing `proof-smoke.spec.ts` pattern)

```typescript
async function seedDemoSession(page: Page, role: string): Promise<void> {
  await page.addInitScript(
    ({ role, token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role", role);
      sessionStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.role", role);
      localStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.demo.role", role);
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}
```

### Environment variables

```bash
VITE_DEV_BASE_URL=http://localhost:3000       # default
CROWN_DEMO_SCHOOL_ID=19801b59-8c05-4c84-9312-5d792e4e839d
CROWN_DEMO_TOKEN=playwright-demo-token
```

### Test selectors to use

```typescript
// Grid present
await expect(page.locator('[data-testid="dashboard-grid"]')).toBeVisible();

// Specific widget
await expect(page.locator('[data-widget-key="enrollment_snapshot"]')).toBeVisible();

// Error banner absent
await expect(page.locator('[role="alert"]')).not.toBeVisible();

// Drilldown drawer
await page.locator('[aria-label="View details for School Health"]').click();
await expect(page.locator('[aria-modal="true"]')).toBeVisible();
await page.keyboard.press("Escape");
await expect(page.locator('[aria-modal="true"]')).not.toBeVisible();

// Heading
await expect(page.getByText("Admin Dashboard")).toBeVisible({ timeout: 8000 });
```

---

## 12. Contract Tests

**File**: `backend/crown_api/tests/test_dashboards_role_contract.py`  
**Count**: 25 tests, all passing as of `dd3f8822`

### Test matrix

| Test | What it checks |
|------|---------------|
| `test_unauthenticated_returns_401` (×4 endpoints) | All 4 endpoints return 401/403 for anon requests |
| `test_missing_school_header_returns_400` (×4) | Missing `X-School-Id` → 400 |
| `test_invalid_school_uuid_returns_400` (×4) | `not-a-uuid` in header → 400 |
| `test_nonexistent_school_returns_404` (×4) | Valid UUID, no matching School → 404 |
| `test_dashboard_me_returns_schema` | `school_id`, `display_name`, `roles`, `default_route` present |
| `test_dashboard_summary_returns_widgets` | `len(widgets) >= 1` |
| `test_dashboard_summary_widgets_sorted_by_priority` | `priorities == sorted(priorities)` |
| `test_dashboard_summary_widget_schema` | `key`, `type`, `title`, `size`, `priority`, `data` all present |
| `test_dashboard_summary_quick_actions_always_present` | `quick_actions` in all role results |
| `test_dashboard_drilldown_requires_widget_param` | Missing `?widget=` → 400 |
| `test_dashboard_drilldown_returns_schema` | `widget`, `school_id`, `page`, `has_more`, `rows` present |
| `test_dashboard_alerts_returns_list` | `alerts` is a list |
| `test_cross_tenant_access_blocked` | user_a requesting school_b → 404 |

### Running the tests

```powershell
# From repo root
cd backend
..\.venv\Scripts\python.exe -m pytest crown_api/tests/test_dashboards_role_contract.py -q
# Expected: 25 passed
```

---

## 13. Phase B Wiring Targets

All stubs are documented with `# Phase B:` comments in `backend/crown_api/dashboards/summary.py`.

### Priority order for Phase B completion

#### 1. `alerts_flip` widget — real alert counts
```python
# File: backend/crown_api/dashboards/summary.py → _alerts_flip()
# Replace stub with:
from academics.models import Section  # or Attendance model
from finance.models import Invoice    # or AR model

overdue_payments = Invoice.objects.filter(school_id=school_id, status="overdue").count()
at_risk_students = AttendanceRisk.objects.filter(school_id=school_id, level__in=["warn","bad"]).count()
missing_grades   = GradeEntry.objects.filter(school_id=school_id, score__isnull=True).count()
```

#### 2. `missing_work` widget — real assignment data  
```python
# File: backend/crown_api/dashboards/summary.py → _missing_work_table()
from academics.models import Assignment, Submission
# Filter: school_id=school_id, due_date__lt=today, submission__isnull=True
# Group by student, return top 20
```

#### 3. `balances` / `payments_this_month` — finance models
```python
# File: backend/crown_api/dashboards/summary.py
from finance.models import Invoice, Payment
balance_total    = Invoice.objects.filter(school_id=school_id, status__in=["unpaid","overdue"]).aggregate(total=Sum("amount_due"))["total"] or 0
payments_current = Payment.objects.filter(school_id=school_id, created_at__month=today.month).aggregate(total=Sum("amount"))["total"] or 0
```

#### 4. `grades_trend` — gradebook sparkline
```python
# File: backend/crown_api/dashboards/summary.py → _grades_trend()
from academics.models import GradeEntry
# Aggregate by month for last 5 months, group by school_id
# Return {"points": [...], "labels": [...]}
```

#### 5. Drilldown endpoint — real paginated rows
```python
# File: backend/crown_api/dashboards/views.py → DashboardDrilldownView.get()
DRILLDOWN_HANDLERS = {
    "alerts_flip":           _drilldown_alerts,
    "enrollment_snapshot":   _drilldown_enrollment,
    "missing_work":          _drilldown_missing_work,
    "attendance_risk":       _drilldown_attendance_risk,
    "balances":              _drilldown_balances,
}
handler = DRILLDOWN_HANDLERS.get(widget_key)
if not handler:
    return Response({"detail": f"No drilldown for {widget_key!r}"}, status=404)
rows, has_more = handler(school_id, page=int(request.GET.get("page", 1)))
```

---

## 14. File-by-File Change Summary

### Files created (Phase 10)

| File | LOC | Purpose |
|------|-----|---------|
| `backend/crown_api/dashboards/serializers.py` | 52 | DRF contract serializers |
| `backend/crown_api/dashboards/summary.py` | 334 | Widget builder service |
| `backend/crown_api/dashboards/views.py` | 165 | API views (4 endpoints) |
| `backend/crown_api/tests/test_dashboards_role_contract.py` | 216 | 25 contract tests |
| `frontend/dashboards/src/api/dashboards.js` | 82 | API client |
| `frontend/dashboards/src/components/dashboard/StatWidget.jsx` | ~80 | KPI tile |
| `frontend/dashboards/src/components/dashboard/FlipWidget.jsx` | ~120 | 3D flip card |
| `frontend/dashboards/src/components/dashboard/TableWidget.jsx` | ~70 | Data table |
| `frontend/dashboards/src/components/dashboard/QuickActionsWidget.jsx` | ~60 | Action grid |
| `frontend/dashboards/src/components/dashboard/FeedWidget.jsx` | ~75 | Feed list |
| `frontend/dashboards/src/components/dashboard/ChartWidget.jsx` | ~180 | SVG donut+sparkline |
| `frontend/dashboards/src/components/dashboard/DrilldownDrawer.jsx` | ~90 | Slide-in drawer |
| `frontend/dashboards/src/components/dashboard/WidgetDispatcher.jsx` | ~45 | Type router |
| `frontend/dashboards/src/pages/RoleDashboardPage.jsx` | 177 | Unified role page |
| `frontend/dashboards/tests/ui/dashboard-smoke.spec.ts` | 139 | Playwright smoke |

### Files modified (Phase 10)

| File | Change |
|------|--------|
| `backend/crown_api/dashboards/urls.py` | Added 4 new `path()` entries under existing 3 legacy paths |
| `frontend/dashboards/src/routes/router.jsx` | Added `import RoleDashboardPage` + `/dash/:role` route (before existing routes) |
| `backend/comms/api/views.py` | Fixed `IndentationError` in `except` block (line 132) |

---

## 15. Guardrails for Future Work

These rules apply to everything in `crown_api/dashboards/`:

1. **Never rename a widget key** after the feature is in prod — frontend components and tests target `data-widget-key` attributes.  
2. **Never remove the legacy endpoints** (`dashboards/admissions/funnel/`, `dashboards/finance/summary/`, `dashboards/academics/enrollment/`) — existing consumers depend on them.  
3. **Always scope DB queries to `school_id`** in `summary.py` — every query must include `.filter(school_id=school_id, ...)`.  
4. **Use `get_dashboard_school_id(request)`** (not `get_request_school_id`) for all dashboard views — it uses `CANONICAL_SCHOOL_HEADER` and has the dashboard-specific cross-tenant logic.  
5. **`_resolve_role()` reads `user.role` first** — do not change this order; the demo header fallback is opt-in via env var.  
6. **New widget types must be added to `DashboardWidgetSerializer.type` ChoiceField** before shipping — the contract test validates this.
