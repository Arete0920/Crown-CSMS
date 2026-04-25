# Curriculum Segment Demo Script
**Demo Date: Feb 28, 2026**
**Segment Length: 8–12 minutes**
**Narrative: Mission-driven curriculum with pacing analytics**

---

## PRE-DEMO CHECKLIST (Run Day-Of, ~90 minutes before)

```powershell
# Terminal 1: Reset and seed (takes ~45 seconds)
cd c:\Users\JMega\OneDrive\Desktop\Crown2026
.\PRE_DEMO_RESET_AND_SEED.ps1 -Force

# Terminal 2: Verify tests pass (takes ~10 seconds)
cd .\backend
python -m pytest -q tests/test_curriculum_pacing.py
# Expected: ".. [100%] 2 passed in ~8.5s"
```

**If both succeed with exit code 0:**
✅ Database is fresh and seeded
✅ Scoping is enforced
✅ Routes are live
✅ Clear to proceed with demo

**If either fails:**
- Reset failed? → Check DB connection + logs
- Tests failed? → Run `pytest -v` to see which assertion broke
- Do NOT proceed; troubleshoot first

---

## SETUP (10 minutes before show)

### 1. Build Frontend (if needed)
```powershell
cd c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards
npm run build
```
Expected output: `dist/` folder with index.html

### 2. Verify Server is Running
```powershell
cd c:\Users\JMega\OneDrive\Desktop\Crown2026\backend
python manage.py runserver 127.0.0.1:8000 --noreload
```
Expected: `Starting development server at http://127.0.0.1:8000/`

### 3. Open Browser (Incognito, Fresh Session)
- URL: `http://127.0.0.1:8000/`
- **Do NOT pre-login** — let demo auto-login handle it

### 4. Screenshot Backup (Insurance)
- Open `/academics` page
- Screenshot the curriculum pacing card (entire card visible)
- Save as: `DEMO_BACKUP_PACING_CARD_[DATE].png`
- If browser glitches during demo, narrator can reference image

---

## DEMO FLOW (8–12 minutes)

### **SEGMENT 0: Context Setup** (1 minute, 0:00–1:00)

**Narrator says:**

> "We've built a curriculum framework for Christian schools. This is bigger than just lessons—it's about pacing. We need to know: is instruction staying on schedule? Are we falling behind?
>
> Let me show you what that looks like."

**On screen:**
- App is loading (`http://127.0.0.1:8000/`)
- Auto-login is happening silently (user should NOT see login form)
- (If login form appears: **FALLBACK**: Click "Login" → username: `head@crown-demo.local` / password: `demo1234`)

**Action:**
- Wait for dashboard to load
- Do NOT click anything yet

---

### **SEGMENT 1: Navigate to Academics** (1 minute, 1:00–2:00)

**Narrator says:**

> "Let's go to the academics dashboard where teachers see their courses and pacing data."

**On screen:**
- You're on the home page or dashboard
- Look for "Academics" nav item (top menu or sidebar)

**Action:**
1. Click **Academics** (or navigate to `/academics`)
2. Wait for page to fully load (you should see course lists, student data, etc.)

**What you should see:**
- ✅ Multiple sections visible (MATH-101-SPRING, ENG-101-SPRING, etc.)
- ✅ Student enrollments listed
- ✅ Curriculum Pacing card near the top (after 1–2 seconds of API load)

**Fallback:**
- If card doesn't appear after 5 seconds: Check browser console (F12)
- If error: narrator can say "Let me reload" and F5
- Do NOT proceed more than 10 seconds of waiting

---

### **SEGMENT 2: Introduce the Curriculum Card** (2 minutes, 2:00–4:00)

**Scroll to Curriculum Pacing Card** (if needed)

**Narrator says:**

> "Here's the curriculum pacing view. Each row represents one of our four active courses. The percentage shows—out of all planned lessons—how many are 'due' by today's date.
>
> We set lesson dates 14 days in advance and distribute them across the unit. So BIB-09 has 20 lessons total, spread from Feb 2 to Feb 27. Today is Feb 16, so 11 of those 20 are past or present. That's 55% complete.
>
> This isn't a perfection metric. It's a reality check: 'Are we on pace, or are we drifting?'"

**On screen (for each course):**
- Card shows: **Course Code** | **Course Name** | **Progress Bar** | **Percentage**
- Example row: `BIB-09 | Bible 9: Foundations | ████░░░░░░░░░░░░░░░░ | 55%`

**Narrator continues:**

> "Notice these aren't all at 100%. That's intentional. Realistic pacing shows variation. ENG-101 might be 60%, MATH-101 at 50%. Schools need to see where they actually are, not where they wish they were."

**Duration**: Let this sink in. Pause for 5–10 seconds so investors read the numbers.

---

### **SEGMENT 3: Technical Depth** (2 minutes, 4:00–6:00)

**Narrator says:**

> "Under the hood, this is school-scoped. Every API call includes the school ID. If you're School A, you see School A's curriculum. School B's data is invisible. That's not just privacy—it's multi-tenant architecture.
>
> The data is read-only in this view. The UI is pulling from a nested JSON structure: each course contains units, each unit contains lessons. Lessons have planned dates, objectives, activities, assessment strategies, even scripture references for each unit.
>
> This is serious curriculum design for Christian schools, not a checkbox feature."

**Optional:** Show browser DevTools Network tab (F12 → Network) and refresh to show:
- ✅ `GET /api/curriculum/courses/pacing-summary/` returns 200
- ✅ Header: `X-School-Id: [uuid]`
- ✅ Response shows 4 courses with nested structure

**If technical depth feels forced:**
- Skip the DevTools part
- Keep it to the narrative above
- Move to next segment

---

### **SEGMENT 4: Show the Data Structure** (Optional, 2 minutes, 6:00–8:00)

**Advanced investors or tech stakeholders might ask:**
> "Can we see the full curriculum structure, not just pacing?"

**If asked, show the nesting:**

1. Click on a course row (if detail drawer is implemented—see below)
   - Card expands to show **Units** under that course
   - Each unit shows: **Title** | **Essential Question** | **Worldview Focus**
   - Each unit has **Lessons** nested under it
   - Each lesson shows: **Title** | **Planned Date** | **Status** (if implemented)

2. Example expansion:
   ```
   BIB-09: Bible 9 - Foundations
   ├─ Unit 1: Covenant Foundations
   │  ├─ Lesson 1: Creation Narrative (Feb 2)
   │  ├─ Lesson 2: Covenant Promise (Feb 3)
   │  └─ ... 3 more lessons
   ├─ Unit 2: Redemptive History
   │  ├─ Lesson 6: Abraham's Call (Feb 9)
   │  └─ ... 4 more lessons
   └─ ... 2 more units
   ```

3. **Narrator says:**
   > "This nested structure is baked into the API. Teachers can eventually drill down and mark lessons complete as they teach. For now, it's read-only—we're tracking planned schedule vs. actual progress."

**If detail drawer is NOT implemented yet:**
- Narrator says: "The full curriculum structure lives in the database. For now, we're showing the pacing summary to investors. Teachers will see the unit/lesson detail in a future release."
- Skip to SEGMENT 5

---

### **SEGMENT 5: Financial/Operational Context** (1 minute, 8:00–9:00)

**Narrator says:**

> "Here's why this matters: pacing drives parent communication. If Bible 9 is falling behind, the head of school knows it now, not in March. That affects tuition messaging, parent guides, and student expectations.
>
> This data ties directly to grades, assessment, and attendance. We're building a connected view of the whole student experience.
>
> And it works across 300 students, multiple terms, multiple schools—all scoped by school ID. No data leakage. No performance hit."

**Narrator continues:**

> "The pacing percentages you see—55%, 60%—are real. Deterministic. Every time we reset the demo, the seed produces the same lesson dates. That means we can rehearse, we can test, we know exactly what investors will see."

---

### **SEGMENT 6: Close** (1 minute, 9:00–10:00)

**Narrator says:**

> "Christian schools are data-light. They inherit crude spreadsheets from public ed or nothing at all. We're building something different: thoughtful, intentional, mission-aligned.
>
> That's what the curriculum framework represents. Not just what's taught, but *how it's paced, tracked, and communicated* to families."

**On screen:**
- Leave the pacing card visible
- Investors take a final screenshot or mental note

**Transition to next segment (if any):**
- "Now let's look at admissions..." (or whatever comes next)
- OR: "Questions on curriculum?"

---

## FALLBACK PATHS

### **Browser doesn't auto-login**
1. Click "Login" button
2. Username: `head@crown-demo.local`
3. Password: `demo1234`
4. Should redirect to `/academics` automatically

### **Curriculum card doesn't load after 10 seconds**
1. Press F5 (browser refresh)
2. If still blank: Open F12 DevTools → Console
3. Check for error messages (auth, network, school context)
4. If school context missing: Narrator says "Let me select the school" and refreshes again
5. If persists: Use screenshot backup to narrate from image

### **Progress bar percentages look wrong (e.g., 100% instead of 55%)**
1. Do NOT try to fix live
2. Narrator says: "We're seeing the expected pacing—these aren't 100% because lessons are spread across the month"
3. Screenshot the card anyway (as proof)
4. Move to next segment; troubleshoot after demo

### **Port 8000 already in use**
1. Kill conflicting process: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
2. Use alt port: `python manage.py runserver 127.0.0.1:8001 --noreload`
3. Update browser URL to `http://127.0.0.1:8001/`
4. Continue demo

### **Database is stale or inconsistent**
1. Run reset again: `.\PRE_DEMO_RESET_AND_SEED.ps1 -Force`
2. Wait for exit code 0
3. Refresh browser
4. If still broken: Check logs for seed errors (`python manage.py seed_heritage_realism_pack --no-comms`)

---

## TIMING TARGETS

| Segment | Duration | Cumulative |
|---------|----------|-----------|
| Context (0) | 1 min | 1:00 |
| Navigate (1) | 1 min | 2:00 |
| Card intro (2) | 2 min | 4:00 |
| Technical (3) | 2 min | 6:00 |
| Data structure (4, opt) | 2 min | 8:00 |
| Ops context (5) | 1 min | 9:00 |
| Close (6) | 1 min | 10:00 |

**Target: 8–12 minutes** (segments 0–3 and 5–6 = 8 min; add segment 4 for 10 min; pad for questions = 12 min max)

---

## SUCCESS CRITERIA

✅ **Auto-login works** (user sees dashboard, no form)
✅ **Curriculum card loads** (4 courses visible within 5 seconds)
✅ **Progress bars render** (~55%, ~60%, etc., not 100%)
✅ **Narrator nails the pacing story** (realistic, mission-aligned, not checkbox)
✅ **No console errors** (F12 shows no red errors)
✅ **Data persists across reload** (refresh page, card still shows same values)

If all ✅: Segment is locked for Feb 28.

---

## REHEARSAL CHECKLIST (Use for 2 full run-throughs + timed runs)

- [ ] Pre-demo check: reset + pytest both pass
- [ ] Frontend built
- [ ] Server running
- [ ] Browser open (incognito)
- [ ] Screenshot backup taken
- [ ] Navigate to /academics (within 10 sec)
- [ ] Curriculum card visible (within 5 sec)
- [ ] Progress bars render correctly (~55% range)
- [ ] Narrator delivers all 6 segments (time self)
- [ ] No console errors
- [ ] Refresh page, data persists
- [ ] Demo under 12 minutes

**Rehearsal 1:** Cold start, full narration, full timing
**Rehearsal 2:** Cold start, full narration, full timing
**Timing run 1:** Timed 10 minutes (segments 0–3, 5–6)
**Timing run 2:** Timed 20 minutes (segments 0–4, 5–6, with Q&A)

---

## NOTES FOR NARRATOR

- **Tone:** Confident, deliberate. Christian schools are serious clients.
- **Pacing:** Slow down on the 55% explanation. Investors expect 100% and might miss context.
- **Numbers:** Use real seed values (4 courses, 20 lessons BIB-09, 55% on Feb 16). Don't improvise.
- **Fallbacks:** If something breaks, stay calm. You have backups (screenshot, reset command, browser refresh).
- **Depth:** Offer technical detail only if asked. Lead with narrative, not DevTools.

---

## POST-DEMO

1. Capture final screenshot of pacing card
2. Note any user questions (for next iteration)
3. Save browser console output (in case errors occurred)
4. Run reset again to verify clean state
5. Commit feedback to [DEMO_IMPROVEMENTS.md](DEMO_IMPROVEMENTS.md) if new ideas emerge

