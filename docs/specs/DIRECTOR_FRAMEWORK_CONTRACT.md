# 🧭 DIRECTOR_FRAMEWORK_CONTRACT.md
**Crown Christian School Management Solutions**
**Director Dashboard Framework – Contract v1.0 (LOCKED)**

This contract governs all Director dashboards under the `/director/` route family.
It ensures every director module follows the same gold-standard pattern anchored at:

- `anchor-financial-aid-director-v1`

If any director dashboard deviates from this contract, it is not considered production-ready.

---

## 🎯 PURPOSE

Director dashboards exist to provide:
1) A calm, text-first, workflow-driven view of "what needs attention now"
2) A consistent layout and interaction model across all Director personas
3) Stable API shapes so UI components are reusable and predictable

---

## ✅ CANONICAL ROUTES (REQUIRED)

Each Director persona MUST support:

### A) HTML Dashboard Page
- `GET /director/<persona>/`

Example:
- `GET /director/admissions/`
- `GET /director/aid/`

### B) JSON APIs (Three Required Endpoints)
- `GET /director/<persona>/api/priority-queue/`
- `GET /director/<persona>/api/metrics/`
- `GET /director/<persona>/api/timeline/`

Example:
- `/director/admissions/api/priority-queue/`
- `/director/admissions/api/metrics/`
- `/director/admissions/api/timeline/`

---

## 🔐 AUTH & PERMISSION (NON-NEGOTIABLE)

### Required Rules
- All `/director/<persona>/` pages require authenticated access.
- All `/director/<persona>/api/*` endpoints require authenticated access.
- Persona access MUST be enforced server-side.

### Forbidden
- ❌ "Hide controls in the UI" as the only permission layer
- ❌ Template-only permission logic
- ❌ Returning data to unauthorized users

### Expected Behavior
- Unauthorized persona → `403 Forbidden`
- Not logged in → redirect to login OR `401` depending on the app standard

---

## 🧱 UI STANDARD (MUST FOLLOW CROWN_UI_CONTRACT.md)

All Director pages MUST follow:
- `CROWN_UI_CONTRACT.md`

### Required Page Layout Order
1. H1 Page Title (e.g., "Admissions Director")
2. Optional subtitle (single-line context)
3. One Primary Action (optional; only if truly necessary)
4. Content blocks in this order:
   - Priority Queue (HERO)
   - Metrics (summary-only; no clutter)
   - Timeline (recent events; actionable context)
5. Secondary actions last

### Forbidden UI Patterns
- ❌ icon-only navigation/buttons
- ❌ popups/modals for core workflow actions
- ❌ charts that do not change a decision today
- ❌ color-only meaning (must include text labels)

---

## 📌 PRIORITY QUEUE (HERO REQUIREMENT)

The Director dashboard MUST include a "Priority Queue" table that answers:

1) What needs attention today?
2) Why is it priority?
3) What's the next action?

### Required Table Columns (Standard)
- Application / Item
- Submitted / Created
- Waiting (days)
- Status
- Reason (explicit text)
- Action (verb button/link)

### Priority Rules
- Priority indicators must be explicit and text-based
- Ordering must be deterministic and explainable

---

## 📡 API RESPONSE SHAPES (STRICT)

All Director APIs must return stable, predictable JSON.

### A) Priority Queue API
Endpoint:
- `GET /director/<persona>/api/priority-queue/`

Response:
```json
{
  "persona": "admissions",
  "generated_at": "ISO-8601",
  "rows": [
    {
      "id": 123,
      "label": "Family Name / Applicant",
      "submitted_date": "ISO-8601",
      "days_waiting": 7,
      "status_label": "Incomplete",
      "priority_label": "High",
      "priority_reason": "Missing documents",
      "next_action_label": "Request Documents",
      "next_action_url": "/.../123/"
    }
  ]
}
```

Notes:
- `rows` is REQUIRED (may be empty, never omitted)
- `priority_reason` is REQUIRED when `priority_label` exists
- `next_action_label`/`url` must be present for actionable items

### B) Metrics API
Endpoint:
- `GET /director/<persona>/api/metrics/`

Response:
```json
{
  "persona": "admissions",
  "generated_at": "ISO-8601",
  "metrics": {
    "total_open": 0,
    "new_this_week": 0,
    "overdue": 0
  }
}
```

Rules:
- `metrics` is REQUIRED
- Keep metrics minimal and decision-supporting
- Do not add vanity metrics

### C) Timeline API
Endpoint:
- `GET /director/<persona>/api/timeline/`

Response:
```json
{
  "persona": "admissions",
  "generated_at": "ISO-8601",
  "events": [
    {
      "timestamp": "ISO-8601",
      "title": "Application submitted",
      "detail": "Family X submitted Grade 6 application",
      "severity": "info",
      "url": "/.../"
    }
  ]
}
```

Rules:
- `events` is REQUIRED (may be empty)
- Timeline is for context and action, not noise

---

## 🧩 SHARED TEMPLATE STRATEGY (PREFERRED)

Director dashboards SHOULD use a shared template such as:
- `director_dashboard.html`

Differences between director personas should be driven by context:
- `director_title`
- `director_subtitle`
- `primary_action_label`/`url`
- `priority_rows`
- `metrics`
- `timeline_events`

Avoid forking templates unless there is a hard requirement.

---

## 🧪 VALIDATION CHECKLIST (REQUIRED BEFORE MERGE)

A Director module is considered complete only if:
- ✅ `/director/<persona>/` returns HTML successfully
- ✅ Priority Queue API returns JSON with required keys
- ✅ Metrics API returns JSON with required keys
- ✅ Timeline API returns JSON with required keys
- ✅ Unauthorized persona returns 403 for all endpoints
- ✅ Layout complies with CROWN_UI_CONTRACT.md
- ✅ No template errors / missing context variables
- ✅ No hardcoded environment paths

---

## 🏁 VERSIONING & ANCHORS

When a Director dashboard reaches "gold standard":

Tag it in Git as an anchor:

Example:
- `anchor-admissions-director-v1`
- `anchor-financial-aid-director-v1`

Anchors exist to prevent drift and provide known-good rollback points.

---

## FINAL RULE

Director dashboards must feel familiar across roles.
If a new director module "feels different," it has drifted.

This contract is the guardrail.
