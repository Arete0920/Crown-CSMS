# PROOF: UI Academics Roster Drawer (PR #100)

**Date:** 2026-02-10
**PR:** #100 (`spine/ui-academics-roster-drawer`)
**Status:** MERGED ✅
**Endpoint:** `GET /api/v1/academics/sections/<SECTION_ID>/roster/`

---

## Runtime Tenant Header Proof (Local)

### Test Environment
- **Frontend:** http://localhost:3000 (Vite dev server)
- **Backend:** http://127.0.0.1:8000 (Django runserver)
- **Browser:** Chrome/Edge DevTools

### Test Steps
1. ✅ Open Dev JWT Panel (bottom-right)
2. ✅ Login with valid credentials
3. ✅ **Set School ID** in the optional field (required for tenant scoping)
4. ✅ Navigate to Academics Dashboard
5. ✅ Open DevTools (F12) → Network tab
6. ✅ Click any "N students" button
7. ✅ Filter for `/roster/` request
8. ✅ Inspect Request Headers

### Observed Results

**Request URL:**
```
GET http://127.0.0.1:8000/api/v1/academics/sections/<SECTION_ID>/roster/
```

**Status Code:** `200 OK`

**Request Headers (Verified):**
```
Authorization: Bearer <JWT_TOKEN>
X-School-Id: <SCHOOL_UUID>
```

✅ **Both headers present** — Tenant scoping confirmed at runtime.

---

## Code Path Verification

### Header Injection (authClient.js:63-65)
```javascript
const schoolId = getSelectedSchoolId();
if (schoolId && !headers.has("X-School-Id")) {
  headers.set("X-School-Id", schoolId);
}
```

✅ **Confirmed:** All `authenticatedFetch` calls automatically inject `X-School-Id` when `getSelectedSchoolId()` returns a value.

### API Client (academics.js:65-69)
```javascript
export function fetchSectionRoster(sectionId) {
  if (!sectionId) throw new Error('sectionId is required');
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/${encodeURIComponent(sectionId)}/roster/`);
}
```

✅ **Confirmed:** Uses `_fetchJson` → `authenticatedFetch` → header injected.

---

## UI Behavior Verification

### Drawer Open/Close Flow
1. ✅ Click "N students" button → Drawer slides in from right
2. ✅ Header shows `section_name` + `course_code`
3. ✅ Metadata displays `term` (nullable) and `teacher` (nullable)
4. ✅ Count badge shows enrolled students count
5. ✅ Student list renders in deterministic order
6. ✅ Close button (✕) dismisses drawer
7. ✅ No console errors

### Defensive Guards (Verified)
- ✅ Optional chaining: `rosterData?.counts?.students`
- ✅ Nullish coalescing: `?? rosterData?.students?.length ?? 0`
- ✅ Safe mapping: `(rosterData?.students ?? []).map(...)`
- ✅ Error fallback: `err?.message || (typeof err === 'string' && err) || 'Failed to load roster.'`

---

## CI Pipeline (All Green)

**PR #100 Checks:**
- ✅ Secret Scan (11s)
- ✅ Spine Audit (7s)
- ✅ pytest (push, 1m50s)
- ✅ pytest (pull_request, 1m50s)
- ✅ Proof Ceremony (1m9s)
- ✅ CI - Tests and Checks / test (53s)
- ✅ CI - Tests and Checks / verify-immutable-tags (7s)

**Total:** 7/7 checks passing ✅

---

## Files Changed

```
frontend/dashboards/src/api/academics.js           |   5 +
frontend/dashboards/src/pages/AcademicsDashboard.jsx | 178 ++++++++++++++++++
2 files changed, 182 insertions(+), 1 deletion(-)
```

---

## Commit SHA

```
f871eb91 - feat(ui/academics): add section roster drawer with defensive guards
```

---

## Grade

✅ **GREEN** — Full end-to-end flow proven:
- Backend endpoint shipping (PR #98 + #99)
- Frontend drawer wired (PR #100)
- Tenant scoping via X-School-Id header confirmed
- All CI checks passing
- Defensive programming patterns applied throughout
- No console errors, no runtime failures

---

## Next Steps

**Optional Follow-up:**
- Add unit tests for drawer component (if React Testing Library available)
- Add E2E test for roster drawer flow (if Playwright/Cypress available)
- Monitor user feedback for edge cases

**Immediate:**
- ✅ PR merged
- ✅ Branch deleted
- ✅ Main updated
- 🎉 **Feature complete**
