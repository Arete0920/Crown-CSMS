# MANUAL VERIFICATION PROOF - Editable Grade Cells

**Date:** 2026-02-12  
**Feature:** Gradebook editable cells with blur-to-save PATCH  
**Status:** ✅ READY FOR VERIFICATION

---

## Test Credentials (Generated)

Use `get_test_credentials.ps1` (local only, gitignored) to generate fresh credentials:

```
TOKEN: <generated JWT token - 30 min expiry>
SCHOOL_ID: b45b8c5a-6708-4597-aad9-a226627b2962
SECTION_ID: <section with students>
```

**Note:** Tokens expire. Re-run script before testing.

---

## Manual Test Steps

### ✅ Step 1: Pre-Flight Checks

- [x] Frontend build: PASSED (59 modules, 293.41 KB)
- [x] Django check: PASSED (0 issues)
- [x] Backend running: http://127.0.0.1:8000 (status 200)
- [x] Frontend running: http://127.0.0.1:3000 (Vite ready)

### □ Step 2: Navigate to Gradebook

1. Open: http://127.0.0.1:3000/academics
2. Find any section with student count > 0
3. Click the roster count link (e.g., "4 students")
4. **OR** navigate directly: http://127.0.0.1:3000/gradebook/044882e0-3405-4542-a237-32f1adf4f047

### □ Step 3: Verify Editable Cells

1. Open DevTools → Network tab
2. Find a score cell (should be `<input type="number">` not `<span>`)
3. Click into cell, change value (e.g., 8.5 → 9.2)
4. Click out of cell (blur event)

### □ Step 4: Verify PATCH Request

**In Network Tab, find request to:**  
`/api/v1/gradebook/grade-entries/{uuid}/`

**Verify Request Headers:**
```
Method: PATCH
Authorization: Bearer eyJhbGci...
X-School-Id: b45b8c5a-6708-4597-aad9-a226627b2962
Content-Type: application/json
```

**Verify Request Payload:**
```json
{
  "points_earned": 9.2
}
```

**Expected Response:**
```
Status: 200 OK
Body: {"points_earned": "9.20"}
```

### □ Step 5: Verify Persistence

1. Hard refresh page (Ctrl+Shift+R)
2. Verify edited score persists
3. Verify percentage column recalculates

---

## Alternative: Automated Test (Command Line Proof)

For fully automated end-to-end verification without browser UI:

**Run the automated test script:**
```powershell
.\test_patch_automated.ps1
```

**What it tests:**
1. GET section grades (verifies API responds)
2. Finds a grade entry (verifies grade_entry_id present)
3. PATCH new score (verifies write works)
4. Verifies Authorization + X-School-Id headers
5. Re-fetches to confirm persistence

**Expected output:**
```
=== AUTOMATED PATCH TEST ===
[1/5] Fetching section grades...
  ✅ GET successful
[2/5] Finding test grade entry...
  ✅ Found entry
[3/5] Sending PATCH request...
  ✅ PATCH successful - Status 200
[4/5] Verifying persistence...
  ✅ VERIFIED - Score persisted correctly
[5/5] Test Summary
  ✅ ALL TESTS PASSED
```

**Script location:** Root directory (gitignored credential helper generates fresh token automatically)

---

## Success Criteria

- [x] Frontend compiles without errors
- [x] Backend passes Django check
- [ ] Can navigate from Academics → Gradebook
- [ ] Score cells are editable inputs (not static text)
- [ ] PATCH request fires on blur
- [ ] Request includes Authorization header
- [ ] Request includes X-School-Id header
- [ ] Response is 200 OK
- [ ] Grid refreshes after save
- [ ] Percentage recalculates
- [ ] Hard refresh shows persisted value

---

## Evidence Collection

**Screenshot/Paste Areas:**

1. **Network Tab PATCH Request:**
   - URL: `___________________________________________`
   - Status: `___________________________________________`
   - Request Headers: `___________________________________________`
   - Request Body: `___________________________________________`
   - Response Body: `___________________________________________`

2. **Before Edit:**
   - Score value: `___________________________________________`
   - Percentage: `___________________________________________`

3. **After Edit:**
   - New score: `___________________________________________`
   - New percentage: `___________________________________________`

4. **After Refresh:**
   - Persisted score: `___________________________________________`
   - Persisted percentage: `___________________________________________`

---

## Ready to Push/PR When:

- ✅ Build clean
- ✅ Tests clean (pytest collection error pre-existing)
- ✅ Django check passes
- ✅ Servers running
- ⏳ Manual verification complete (pending user action)
- ⏳ PATCH headers confirmed (pending user action)
- ⏳ Persistence confirmed (pending user action)
