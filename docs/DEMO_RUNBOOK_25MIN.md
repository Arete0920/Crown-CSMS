# Crown2026 Demo Runbook — 25-Minute Scripted Walkthrough

**Audience:** Mixed stakeholders — Investor, Head of School, Board member  
**Duration:** ~25 minutes (with Q&A headroom)  
**Last validated:** 2026-03-01  
**Demo user:** `playwright@crown-demo.local`  
**Demo school:** Heritage Christian Academy

---

## Pre-Demo Setup (10 minutes before)

Run the audit gate FIRST. If it fails, do not proceed.

```powershell
# Run from repo root (Crown2026/)
pwsh tools/demo_audit/run_demo_audit.ps1
```

If the script exits 0 (green), proceed. If it exits 1 (red), read the FAIL items and fix them.

### Start Vite WITH demo mode (suppresses debug panel)

```powershell
Set-Location frontend\dashboards
$env:VITE_API_BASE    = "https://crown-api-prod.azurewebsites.net"
$env:VITE_DEMO_MODE   = "1"
npm run dev
```

> **Critical:** `VITE_DEMO_MODE=1` MUST be set. Without it, a DevJwtPanel debug overlay appears on every page.

### Browser prep

- Use **Chrome or Edge** (not VS Code Simple Browser)
- Open a fresh profile or Incognito window
- Navigate to: `http://localhost:3000/login`
- Zoom: 90% (Ctrl+-) for better widget visibility
- Open two tabs pre-loaded: `http://localhost:3000/login` and `http://localhost:3000/admin`

### Login credentials (memorize these)

| Field       | Value                       |
|-------------|---------------------------- |
| Email       | `playwright@crown-demo.local` |
| Password    | `PlaywrightDemo1!`           |
| Role        | Director → lands on `/admin` |

---

## Demo Script — 25 Minutes

### Opening (0:00 – 1:00) — Set the stage

> "What you're about to see is a unified school operating platform — one login, every persona, every workflow. No switching tools, no spreadsheets, no emailed reports."

**Action:** Log in  
URL: `http://localhost:3000/login`  
Fill email + password → Submit  
**Expected:** Redirects to `/admin` within 3 seconds.

---

### Segment 1: School Operations Overview (1:00 – 5:00)

**Route:** `http://localhost:3000/admin`

> "This is the Director view — real-time pulse of the entire school."

**Show:**
- Enrollment count widget
- Financial health summary tile
- Attendance snapshot
- Any alerts/notifications panel

> "Every number here is live — pulled from our production database right now."

**If a widget shows a spinner longer than 5 seconds → move on, say:**  
> "The data loads asynchronously — it's querying the production API in real time."

---

### Segment 2: Admissions Pipeline (5:00 – 9:00)

**Route:** `http://localhost:3000/admissions`

> "Admissions is where revenue begins. Every inquiry, application, and enrollment decision happens here."

**Show:**
1. Inquiry list or pipeline board
2. Filter or stage view (if visible)
3. Point to "convert to applicant" flow

> "From inquiry to enrolled student — fully tracked. No paper, no email chains."

**Key talking points:**
- Real-time pipeline visibility
- Role-based access (admissions staff vs head of school vs board)
- Enrollment decisions link directly to billing obligations

**If list is empty:**  
> "This is our production school — we can see the admissions pipeline for Heritage Christian Academy. The data is school-scoped."

---

### Segment 3: Finance — Billing & Invoices (9:00 – 13:00)

**Routes (visit in order):**

```
http://localhost:3000/finance
http://localhost:3000/billing
http://localhost:3000/financial-aid
```

> "Finance in a school is usually chaos — multiple systems, manual reconciliation. Crown unifies it."

**Show on `/finance`:**
- Revenue summary
- Outstanding balances
- Any ledger summary tiles

**Show on `/billing`:**
- Invoice list
- Family balance view

> "Every obligation, every payment, every outstanding balance — all in one place. No QuickBooks export."

**Show on `/financial-aid`:**
- Aid awards or applications
- Balance impact

> "Financial aid is fully integrated — when an award is applied, the family balance updates instantly."

**If finance shows blank widgets:**  
> "The financial module is live-connected to our production ledger. The numbers you'd see in a full deployment reflect that school's real financial picture."

---

### Segment 4: Academics & Gradebook (13:00 – 17:00)

**Route:** `http://localhost:3000/academics`

> "Academics is where teachers live — attendance, gradebook, curriculum. And where parents worry."

**Show:**
- Course/section list
- Grade summary view

**Navigate to:** `http://localhost:3000/teacher/attendance` (if in demo)

> "Teachers mark attendance here. It flows immediately to the admin report. No phone call to the office."

> "Parents see the same grade data their child's teacher just updated — with no manual sync, no delay."

**Key talking point:**
> "This is the one platform that connects the teacher's gradebook to the parent's phone to the board's enrollment report."

---

### Segment 5: Communications (17:00 – 19:00)

**Route:** `http://localhost:3000/communications`

> "Every school runs on communication. Announcements, alerts, messages — currently living in 6 different systems."

**Show:**
- Announcement board or feed
- Message thread (if present)

> "Crown centralizes it. One place. Role-aware — a board member sees different content than a parent."

---

### Segment 6: Board View (19:00 – 22:00)

**Route:** `http://localhost:3000/board/executive`

> "This is what the board cares about. Not individual grades — the school's health metrics."

**Show:**
- Enrollment trend
- Financial summary
- Operational KPIs

> "A board member can get this in 30 seconds, any time, on any device. No waiting for the monthly report."

**Key investor talking point:**
> "Every school we onboard gets this immediately. No configuration, no consultants. It's built in."

---

### Closing (22:00 – 25:00)

> "What you've seen in 22 minutes is a complete school operating system — admissions, billing, finance, academic records, communications, and board reporting — all connected, all role-aware, all real-time."

> "The average school uses 6–12 disconnected tools to do what Crown does in one login."

**Leave up:** `http://localhost:3000/board/executive`  
(Board view is the strongest visual to leave on during Q&A)

---

## Fallback Playbook — "If This Fails"

| Failure | Symptom | Recovery |
|---------|---------|----------|
| Vite is down | ERR_CONNECTION_REFUSED at localhost:3000 | `Set-Location frontend\dashboards ; $env:VITE_DEMO_MODE="1" ; $env:VITE_API_BASE="https://crown-api-prod.azurewebsites.net" ; npm run dev` (ready in ~3s) |
| Login fails (401) | "Invalid credentials" on login page | Check prod API: `Invoke-RestMethod https://crown-api-prod.azurewebsites.net/api/health/` — if db=ok, try login via API directly |
| Login fails (500) | Server error on login | API is down. Run: `az webapp restart -g crown-rg -n crown-api-prod` then wait 35s |
| Widget blank/spinner | Dashboard card never loads | Click browser refresh once. If still blank, say "live data is loading" and move to next segment |
| Page shows Application Error | React crash | Hard-refresh (Ctrl+Shift+R). If persists, navigate directly to next demo URL |
| DevJwtPanel appears | Debug panel visible | Stop demo momentarily. Kill Vite, restart with `VITE_DEMO_MODE=1`. Takes 10 seconds. |
| API health db=error | Can't reach prod database | Do NOT demo live. Use the local backend: `& .venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000 --noreload` and set `$env:VITE_API_BASE="http://127.0.0.1:8000"` |
| /admissions is blank | No data in prod | Say "scoped to this demo school" and move to finance segment |
| /board/executive blank | Board component not loading | Fall back to `/admin` — same KPIs in director view |

---

## Quick-Reference: Demo Tab Order

Pre-load these tabs before stakeholders enter the room:

```
Tab 1:  http://localhost:3000/login             (start here)
Tab 2:  http://localhost:3000/admin             (school overview)
Tab 3:  http://localhost:3000/admissions        (pipeline)
Tab 4:  http://localhost:3000/finance           (revenue/ledger)
Tab 5:  http://localhost:3000/billing           (invoices)
Tab 6:  http://localhost:3000/financial-aid     (aid awards)
Tab 7:  http://localhost:3000/academics         (gradebook)
Tab 8:  http://localhost:3000/communications    (announcements)
Tab 9:  http://localhost:3000/board/executive   (leave this up at end)
```

---

## Demo Env Health Check (run immediately before demo)

```powershell
# 30-second pre-demo check
$h = Invoke-RestMethod https://crown-api-prod.azurewebsites.net/api/health/
Write-Host "API: ok=$($h.ok) db=$($h.db) sha=$($h.build_sha.Substring(0,8))"
$v = Invoke-WebRequest http://localhost:3000/ -UseBasicParsing -TimeoutSec 5
Write-Host "UI:  HTTP $($v.StatusCode)"
```

Both must return `ok=True / db=ok` and `HTTP 200`.

---

## Hard Stop Criteria (abort demo if any of these are true)

- [ ] API health returns `ok=False` or `db=error`  
- [ ] `http://localhost:3000/login` returns ERR_CONNECTION_REFUSED  
- [ ] Login with demo credentials returns 401 or 500  
- [ ] DevJwtPanel debug overlay is visible on any page  
- [ ] More than 2 dashboard pages show "Application Error"

If any hard stop is true → delay the demo. Do not proceed.

---

_This runbook is generated from and validated against the production state of Crown2026 as of 2026-03-01._
