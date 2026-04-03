# Crown Demo Surface Wiring Spec (Authoritative)
**Purpose:** Prevent "component exists but page 404s" and stop whack-a-mole.
This file is the single source of truth for Tier-1 runtime wiring.

## Non-Negotiable Rules
- A surface is not "done" until it passes ALL gates below.
- "CI green" is not enough. We require reachability + API wiring proof.
- If any Tier-1 gate fails, we fix it before building anything else.

---

# Tier-1 Surfaces (Investor Daily Use)

## S1 — Login / Dev JWT
**Route(s):**
- `/login` (if present) OR `/?dev=1` (if that's how Dev JWT is exposed)

**Must:**
- Provide a working login mechanism that results in:
  - `sessionStorage["crown.jwt.access"]` present (non-empty)
  - `sessionStorage["crown.school.id"]` present (valid UUID)

**Manual Proof:**
- Open app, login, then run in browser console:
  - `sessionStorage.getItem("crown.jwt.access")`
  - `sessionStorage.getItem("crown.school.id")`
Both must return non-empty strings.

---

## S2 — Student360 (Core Deep Link)
**Route:**
- `/students/:id`

**Must Render:**
- Student header (name or "Student" identity block)
- Graduation tile visible (even while loading)

**Must Call:**
- `GET /api/v1/graduation/audit/<student_uuid>/`

**Required Headers:**
- `Authorization: Bearer <token>`
- `X-School-Id: <uuid>`

**Success Condition:**
- HTTP 200 from graduation audit endpoint
- Tile shows chip + progress bar + earned/required numbers (0 allowed)

---

## S3 — Backend Health
**Endpoint:**
- `GET /api/system/health/`

**Success Condition:**
- HTTP 200
- Response includes `"ok": true` OR `"status": "healthy"` (either acceptable)

---

# Required Repo Wiring (Hard Gates)

## GATE R1 — Router Reachability
**File:** `frontend/dashboards/src/routes/router.jsx`

Must contain Tier-1 route definitions:
- `/students/:id` -> `Student360Page`

---

## GATE B1 — Backend URL Registration
Must expose graduation audit route in Django urls:
- `/api/v1/graduation/audit/<uuid>/`

---

# Proof Commands (Local + CI)
These commands are the official proof. All must pass.

## P1 — Route reachability (static)
Run:
- `powershell -ExecutionPolicy Bypass -File tools/verify_demo_surface.ps1 -Mode static`

Pass:
- Script exits 0 with PASS messages.

## P2 — Optional runtime probe (manual)
- Start backend with `CROWN_DEMO_MODE=true`
- Start frontend with `VITE_API_BASE_URL=http://127.0.0.1:8000`
- Open:
  - `http://localhost:3000/students/<KNOWN_STUDENT_UUID>`
- Verify network call for graduation audit:
  - Status 200
  - Both headers present
  - Tile renders

---

# Known Demo Student UUID (refresh as needed)
If you need a current UUID:

Backend:
`python manage.py shell -c "from students.models import Student; s=Student.objects.first(); print(s.id)"`

(If the Student model path differs, update this line in the script below.)
