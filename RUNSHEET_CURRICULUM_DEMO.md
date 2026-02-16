# Curriculum Segment Runsheet
**Investor Demo – Feb 28, 2026**  
**Segment Length: 10 minutes**

---

## PRE-DEMO (90 minutes before)

### Health Check
```
1. Run: cd Crown2026
2. Run: .\PRE_DEMO_RESET_AND_SEED.ps1 -Force
3. Verify: Exit code = 0
4. Run: cd backend && python -m pytest -q tests/test_curriculum_pacing.py
5. Verify: "2 passed"
```

✅ If both green: Clear to proceed  
❌ If either fails: Fix before continuing (see CONTINGENCIES below)

---

## 10-MINUTE DEMO FLOW

### [0:00–1:00] OPEN & LOGIN
1. Browser → `http://127.0.0.1:8000/`
2. App loads, auto-login happens (investor sees NOTHING yet)
3. Wait for page to settle

**Investor sees:** Home page or dashboard

---

### [1:00–2:00] NAVIGATE ACADEMICS
1. Click **Academics** nav item
2. Wait 2–3 seconds for API load (curriculum card loads)

**Investor sees:** Course list, enrollments, etc.
**Card appears:** "Curriculum Pacing" at top with 4 progress bars

---

### [2:00–4:00] INTRODUCE PACING
Read from script (DEMO_SCRIPT_CURRICULUM_SEGMENT.md line 78):

> "Here's the curriculum pacing view. Each row represents one of our four active courses. The percentage shows—out of all planned lessons—how many are 'due' by today's date..."

**Pause 10 seconds** — Let investors read the percentages (55%, 60%, etc.)

Continue:

> "This isn't a perfection metric. It's a reality check: 'Are we on pace, or are we drifting?'"

---

### [4:00–6:00] TECHNICAL DEPTH (Optional Expansion)
If investor asks "Can you show the curriculum structure?" OR if time allows:

1. Click on **any course row** (e.g., BIB-09)
2. Card expands to show units and lessons
3. Say: "Each unit has essential questions and worldview focus tied to scripture. Lessons are planned 14 days in advance..."

**If NOT asked:** Skip and go to [6:00]

---

### [6:00–8:00] OPS/FINANCIAL CONTEXT
Read from script (DEMO_SCRIPT_CURRICULUM_SEGMENT.md line 160):

> "Here's why this matters: pacing drives parent communication. If Bible 9 is falling behind, the head of school knows it now..."

Continue:

> "The pacing percentages you see—55%, 60%—are real. Deterministic. Every time we reset the demo, the seed produces the same lesson dates. That means we can rehearse, we can test, we know exactly what investors will see."

---

### [8:00–10:00] CLOSE
Read from script (DEMO_SCRIPT_CURRICULUM_SEGMENT.md line 180):

> "Christian schools are data-light. We're building something different: thoughtful, intentional, mission-aligned. That's what the curriculum framework represents."

**Leave pacing card visible** on screen

**Transition:** "Questions? Or shall we move on to [next segment]?"

---

## KEY NUMBERS (Reference)
- 4 courses
- 16 units (4 per course)
- 80 lessons (5 per unit)
- Pacing range: 55–70% (NOT 100%)
- Lesson dates: Feb 2–27 (always aligned to "today")

---

## DEMO BACKUP COMMANDS (If Something Breaks)

| Problem | Command | Time |
|---------|---------|------|
| Page blank | F5 (refresh) | 5 sec |
| Curriculum card missing | F5 again | 5 sec |
| API error in console | Run reset again | 45 sec |
| Can't log in | Use fallback: `head@crown-demo.local` / `demo1234` | 10 sec |
| Port 8000 in use | Switch to 8001: `runserver 127.0.0.1:8001` | 30 sec |

---

## CLICK PATH (Exact)

```
[Home] → (auto-login) → [Academics] → (wait 3 sec) → See card → (read narration) → (optional: click course) → (close/Q&A)
```

---

## SUCCESS= INVESTOR SEES

✅ 4 courses listed  
✅ Each with progress bar (green)  
✅ Percentages 50–70% (not 100%, not 0%)  
✅ Dates are sensible (Feb 2–27)  
✅ Card says "As of [today]"  
✅ Narrator explains pacing matters  
✅ (Optional) Expands to show units/lessons  

---

## TIMING NOTES

- Setup & pre-demo check: 15 min
- Demo itself: 10 min
- Q&A buffer: 5 min
- **Total: 30 min from reset to close**

If you have 10 min only: Skip [4:00–6:00] (optional expansion). Do segments 0–3, 5–6.

If you have 20 min: Do all segments with time for 2–3 investor questions.

