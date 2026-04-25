# Curriculum Segment Demo – Complete Prep Package
**Demo Date: Feb 28, 2026**
**Segment Lead: [Your name]**
**Duration: 10 minutes + Q&A**

---

## 📋 What You Need (5 Files)

| File | Purpose | When to Use |
|------|---------|-----------|
| [DEMO_SCRIPT_CURRICULUM_SEGMENT.md](DEMO_SCRIPT_CURRICULUM_SEGMENT.md) | Full script with narration, timing, fallback paths | Read before & during each rehearsal |
| [RUNSHEET_CURRICULUM_DEMO.md](RUNSHEET_CURRICULUM_DEMO.md) | Click-by-click action runsheet | Paste on second monitor during demo |
| [CONTINGENCY_CURRICULUM_DEMO.md](CONTINGENCY_CURRICULUM_DEMO.md) | What to do if X breaks | Keep handy (F12 for DevTools) |
| [FINAL_CURRICULUM_PROOF.txt](../../artifacts/proof/FINAL_CURRICULUM_PROOF.txt) | One-liner validation command | Run 90 min before demo |
| [backend/smoke_test_curriculum_demo.py](../../backend/smoke_test_curriculum_demo.py) | Automated 2-min health check | Run after reset, should show ✅ all 5 |

---

## 🚀 QUICK START (Day Of)

### 90 Minutes Before Demo

```powershell
cd c:\Users\JMega\OneDrive\Desktop\Crown2026

# 1. Reset & seed (45 seconds)
.\PRE_DEMO_RESET_AND_SEED.ps1 -Force
# Expected: "Exit code: 0"

# 2. Health check (8 seconds)
cd backend
python smoke_test_curriculum_demo.py
# Expected: "✅ All 5 checks passed. Demo ready."

# 3. Start server (in SEPARATE terminal)
python manage.py runserver 127.0.0.1:8000 --noreload
# Expected: "Starting development server at http://127.0.0.1:8000/"

# 4. Build frontend (if you changed code)
cd ../frontend/dashboards
npm run build

# 5. Open browser (fresh/incognito)
# Go to: http://127.0.0.1:8000/
# You should see dashboard with curriculum card loaded
```

✅ If all green: Clear to proceed with investors
❌ If any red: Fix using [CONTINGENCY_CURRICULUM_DEMO.md](CONTINGENCY_CURRICULUM_DEMO.md)

---

## 📝 During Demo (10 Minutes)

**Use [RUNSHEET_CURRICULUM_DEMO.md](RUNSHEET_CURRICULUM_DEMO.md) as your action guide.**

1. **[0:00–1:00]** → Open app, auto-login
2. **[1:00–2:00]** → Navigate to Academics
3. **[2:00–4:00]** → Introduce pacing concept (read script)
4. **[4:00–6:00]** → Optional: Expand course to show units/lessons
5. **[6:00–8:00]** → Talk ops/financial impact (read script)
6. **[8:00–10:00]** → Close & transition to next segment

**Total: 10 min + Q&A**

---

## 🛠️ If Something Breaks

**Use [CONTINGENCY_CURRICULUM_DEMO.md](CONTINGENCY_CURRICULUM_DEMO.md).**

Quick reference:
- **Page blank?** → F5 (refresh)
- **Card not showing?** → F5, then check DevTools (F12)
- **Wrong percentages?** → Likely a reset issue, use screenshot backup
- **API 404?** → Route problem, explain delay to investors
- **Auth failure?** → F5 or manual login with `head@crown-demo.local` / `demo1234`

**Screenshot backup:** Before demo, take a screenshot of the curriculum card (all 4 courses visible). If live demo breaks, you can narrate from the screenshot.

---

## 🎬 Rehearsal Plan (12 Days)

### Rehearsal 1 (Full Run, No Timing)
```
1. Run full reset + smoke test
2. Open browser, go through all 6 segments
3. Don't worry about time, just verify everything works
4. Take notes on what feels awkward
```

### Rehearsal 2 (Full Run, No Timing)
1. Same as Rehearsal 1
2. Refine narration, cut anything that doesn't land

### Timing Run 1 (10 minutes)
```
1. Reset + smoke test
2. Go through segments 0–3, 5–6 (skip optional expansion)
3. Time yourself: should be ~8–10 min
4. Note pacing issues
```

### Timing Run 2 (20 minutes)
```
1. Reset + smoke test
2. Go through segments 0–4, 5–6 (include optional expansion)
3. Time yourself: should be ~15–20 min
4. Simulate Q&A at end (5 min)
```

**Target:** 8–10 min without expansion, 15–20 min with expansion

---

## 📊 Key Data to Remember

| Item | Value |
|------|-------|
| Courses | 4 (BIB-09, ENG-101, MATH-101, etc.) |
| Units per course | 4 |
| Lessons per unit | 5 (total: 80) |
| Pacing range | 55–70% (realistic, not 100%) |
| Lesson date range | Feb 2–27 (always aligns to today) |
| Students | 300 (for other segments) |
| Attendance | 1500 records |

---

## 🔒 Locked Behaviors (Don't Break These)

✅ **Reset is non-interactive** (no prompts with `-Force`)
✅ **Seed is deterministic** (same data every run)
✅ **Scoping works** (wrong school gets 0 or 404)
✅ **Frontend guard works** (missing schoolId shows error card)
✅ **Pytest locked** (both scoping tests enforce structure)
✅ **Pacing is realistic** (never 100%)

If you change anything:
```
cd backend
pytest tests/test_curriculum_pacing.py -v
```

Should see: `2 passed`

If you break something, all 5 smoke test checks fail.

---

## 📸 Screenshot Backup

Before demo:
1. Run reset + smoke test
2. Navigate to `/academics`
3. Take screenshot of **entire Curriculum Pacing card**
4. Save as: `DEMO_BACKUP_CURRICULUM_[DATE].png`
5. Keep open in separate window

If live demo breaks badly:
- Narrator: "Let me show you what this looks like"
- Share screenshot
- Point at courses: "BIB-09 at 55%, ENG-101 at 60%..."
- Continue narration

✅ This is an acceptable fallback. Investors see the actual data.

---

## 👥 Investor Q&A (Likely Questions)

| Question | Answer |
|----------|--------|
| "Can teachers mark lessons done?" | "That's next phase. For now, we auto-calculate based on planned dates." |
| "What if lesson dates are wrong?" | "Head of school can edit in admin. We have an import flow for that." |
| "Does this work for other schools?" | "Fully. Each school sees only their own curriculum—school-scoped via API." |
| "Can parents see this?" | "Not yet. For now, it's internal to school admin. Parent view is roadmap." |
| "What about assessments?" | "Each lesson has objective + assessment strategy in the data layer. UI sugar later." |

---

## 🎯 Success Criteria

Demo is **LOCKED AND READY** when:

✅ Reset completes with exit code 0
✅ Smoke test shows "All 5 checks passed"
✅ You can navigate to `/academics` and see card within 3 seconds
✅ Card shows 4 courses with progress bars in 55–70% range
✅ You can click a course and see units/lessons expand
✅ You can say the 6 script segments without stumbling
✅ You have screenshot backup ready
✅ You've rehearsed twice (10 min for timing, 20 min for expansion)

If all ✅: You're locked. Demo will go smoothly.

---

## 📞 Support

**Before Feb 28:** As questions come up, update this package:
- Better narration? → Update [DEMO_SCRIPT_CURRICULUM_SEGMENT.md](DEMO_SCRIPT_CURRICULUM_SEGMENT.md)
- New failure mode? → Add to [CONTINGENCY_CURRICULUM_DEMO.md](CONTINGENCY_CURRICULUM_DEMO.md)
- Timing changes? → Update [RUNSHEET_CURRICULUM_DEMO.md](RUNSHEET_CURRICULUM_DEMO.md)

**Day-of:**
- Stuck? Use [CONTINGENCY_CURRICULUM_DEMO.md](CONTINGENCY_CURRICULUM_DEMO.md)
- Need help? Check [DEMO_SCRIPT_CURRICULUM_SEGMENT.md](DEMO_SCRIPT_CURRICULUM_SEGMENT.md) section "FALLBACK PATHS"

---

## 📅 Timeline

- **Feb 16**: All files created ✅
- **Feb 17–24**: 2 full rehearsals + 2 timing runs
- **Feb 26**: Final validation run
- **Feb 28, T-90min**: Reset + smoke test
- **Feb 28, T-0min**: Go live

---

**This segment is production-ready. You got this.** 🎯

