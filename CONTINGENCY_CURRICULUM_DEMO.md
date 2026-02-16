# Curriculum Segment – Contingency Guide
**What to do when things go wrong during demo**

---

## BEFORE DEMO (Preventive)

### Double-Check Checklist (30 min before)

```powershell
# 1. Reset database
cd Crown2026
.\PRE_DEMO_RESET_AND_SEED.ps1 -Force
# Expected: "Exit code: 0"

# 2. Run smoke test
cd backend
python smoke_test_curriculum_demo.py
# Expected: "✅ All 5 checks passed. Demo ready."

# 3. Build frontend (if you changed it)
cd ../frontend/dashboards
npm run build
# Expected: "dist/" folder with index.html

# 4. Start server (in SEPARATE terminal)
cd ../../backend
python manage.py runserver 127.0.0.1:8000 --noreload
# Expected: "Starting development server at http://127.0.0.1:8000/"

# 5. Open browser (fresh/incognito)
# Go to: http://127.0.0.1:8000/
# Verify: Auto-login happens, you see dashboard
```

**If ANY of these fail:** Do not proceed with demo. Fix and re-run all 5 steps.

---

## DURING DEMO – FAILURE SCENARIOS

### Scenario 1: Page Takes >5 Seconds to Load
**Symptom:** Investor is waiting, nothing is happening

**Most likely cause:** Frontend build is stale or server is slow

**Immediate fix (30-60 sec):**
1. Narrator: "Let me refresh the page"
2. Press **F5** (refresh page)
3. Wait 3–4 seconds
4. If dashboard appears: Continue demo (no explanation needed)
5. If still blank after 10 seconds: Use screenshot backup (see below)

**If stuck:** Skip to Scenario 6

---

### Scenario 2: Curriculum Card Doesn't Appear (Blank Below Course List)
**Symptom:** Dashboard is fine, but no "Curriculum Pacing" card

**Most likely cause:** API call failed silently, or school ID not set

**Check fast (15 sec):**
1. Open DevTools (**F12**)
2. Click **Network** tab
3. Look for `pacing-summary` request
4. If red/failed: API is down
5. If success (200): Check **Console** tab for JS errors (red text)

**Immediate fix:**
- If API failed: Backend is down → restart with `python manage.py runserver 127.0.0.1:8000 --noreload`
- If JS error: Likely auth issue → reload (`F5`) and wait 3 sec

**If stuck >30 sec:** Use screenshot backup

---

### Scenario 3: Curriculum Card Shows 100% (Not ~55%)
**Symptom:** Progress bars are all full, not realistic

**What this means:** Seed didn't include planned_date distribution

**Do NOT try to fix live.** Continue demo:
- Narrator: "These shouldn't be 100%—they should be 50–70%. Let me reload..."
- Press F5
- If still 100% after reload: Use screenshot backup

(This is a seed problem, not a code problem. Reset database if time permits later.)

---

### Scenario 4: Console Shows "School Context Missing"
**Symptom:** Card says "School context missing. Select a school or re-login..."

**Cause:** Session lost, or localStorage cleared

**Immediate fix (10 sec):**
1. Press **F5** (refresh)
2. Wait for auto-login to complete
3. If still shows message: Investor may need to manually log in
   - Click "Login" button
   - Username: `head@crown-demo.local`
   - Password: `demo1234`
   - Click submit

**If manual login works:** Continue normally (takes ~5 sec)

**If manual login fails:** Port or DB issue → see Scenario 7

---

### Scenario 5: API Returns 403 (Forbidden)
**Symptom:** Card shows red error, DevTools shows 403

**Cause:** Auth token missing or expired

**Immediate fix (15 sec):**
1. Press **F5** (refresh entire page)
2. Wait 3 sec for auto-login
3. Verify card appears with data

**If still 403:** Backend auth is broken → restart backend server

---

### Scenario 6: API Returns 404 (Not Found)
**Symptom:** Card shows error, DevTools shows 404 on `/api/curriculum/...`

**Cause:** Route not wired, or wrong backend code deployed

**Do NOT continue.** This is a code problem.

**Explanation for investor:**
> "The endpoint isn't there. This is a backend issue. Let me show you from the code instead..."

**Then:**
1. Open your IDE (VSCode)
2. Show [backend/curriculum/views.py](backend/curriculum/views.py) → `@action` decorators
3. Show [backend/crown_api/urls.py](backend/crown_api/urls.py) → `path("api/curriculum/", include("curriculum.urls"))`
4. Say: "The routes are defined, but something's off in this deployment. We'll fix this before investor day."

---

### Scenario 7: Port 8000 Already in Use
**Symptom:** Can't start server, error says "Port 8000 in use"

**Immediate fix (30 sec):**
```powershell
# Kill the conflicting process
Get-Process | Where-Object {$_.Port -eq 8000}  # (may not work on Windows)

# OR: Use alternate port
cd backend
python manage.py runserver 127.0.0.1:8001 --noreload

# Then update browser URL to:
# http://127.0.0.1:8001/
```

**Continue demo** on port 8001 (works identically)

---

### Scenario 8: Browser Keeps Showing Old Cached Data
**Symptom:** You reset database, but browser still shows old percentages

**Cause:** Browser cache

**Immediate fix (10 sec):**
1. Press **Ctrl+Shift+Del** (or **Cmd+Shift+Del** on Mac)
2. Click "Clear browsing data"
3. Check "Cookies and other site data"
4. Click "Clear data"
5. Refresh page

---

## FALLBACK: Screenshot Backup

**If anything takes >30 seconds to fix:** Use the screenshot backup.

### Before Demo (Create Backup)
1. Run reset + smoke test (make sure everything works)
2. Navigate to `/academics` in browser
3. Screenshot the **entire Curriculum Pacing card** (including all 4 courses)
4. Save as: `DEMO_BACKUP_[DATE].png`
5. Keep this image open in a separate window

### If Demo Breaks
1. Narrator: "Let me show you what this looks like from last week's rehearsal"
2. Click or share the screenshot
3. Point at specific courses: "BIB-09 at 55%, ENG-101 at 60%..."
4. Continue with narration (off-screen)
5. Investors still see the actual data

**This is 100% acceptable.** The narrative and numbers matter, not the live interaction.

---

## POST-DEMO CHECKLIST

1. ✅ Get investor feedback on curriculum segment
2. ✅ Take screenshot of final state (for records)
3. ✅ Save any DevTools network logs (in case of errors)
4. ✅ Note any unexpected questions
5. ✅ Close browser cleanly
6. ✅ Document any breakage in [DEMO_IMPROVEMENTS.md](DEMO_IMPROVEMENTS.md)

If demo failed at any point:
```
cd Crown2026
python backend/smoke_test_curriculum_demo.py
```
This will tell you exactly what's broken so you can fix it for next time.

---

## QUICK REFERENCE: Decision Tree

```
Is the card showing?
├─ YES: Is pacing ~55%?
│  ├─ YES: Continue with narration ✅
│  └─ NO (100%): F5, if still wrong → screenshot backup
└─ NO: Is there an error message?
   ├─ "School context missing": F5, then manual login
   ├─ HTTP 403: F5 (auth token)
   ├─ HTTP 404: Route problem → show code, explain delay
   ├─ Blank with no error: DevTools check for JS errors
   └─ Complete blank: Try F5, if stuck > 10 sec → screenshot
```

---

## NUMBERS TO REMEMBER

- **Database:** 300 students, 1500 attendance, 4 courses, 80 lessons
- **Pacing:** 55–70% range (NOT 100%, NOT 0%)
- **Dates:** Feb 2–27 (always aligns to "today")
- **Routes:** `/api/curriculum/courses/pacing-summary/` + `/{id}/pacing/`
- **Auth:** `head@crown-demo.local` / `demo1234`
- **Server:** `http://127.0.0.1:8000/` (or :8001 if 8000 in use)

---

## WORST CASE: "Play for Time"

If multiple systems are broken and you can't recover:

**Narrator:** "You know what, let me pause and reboot for 3 minutes. Give me the server back..."

(Silently fix in background. Investors get bathroom break / notes break.)

Then restart demo from top. You'll have everything working.

**This is better than limping through a broken 10 minutes.**

