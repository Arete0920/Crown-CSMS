# DEMO_FLOW.md — Click-Path Runbook

**Rollback tag:** `demo-2026-02-18-baseline` (commit `2812e2c9`)

---

## Rehearsal Reset (run before every rehearsal)

```powershell
# 1. Kill stale servers
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Sync main
cd "$env:USERPROFILE\OneDrive\Desktop\Crown2026"
git checkout main
git pull --ff-only

# 3. Migrate check (should print nothing)
cd backend
python manage.py migrate --check

# 4. Seed (idempotent)
python manage.py seed_curriculum_vertical_slice --school-id 19801b59-8c05-4c84-9312-5d792e4e839d

# 5. Start backend
python manage.py runserver 127.0.0.1:8000 --noreload &

# 6. Start frontend (new terminal)
cd "$env:USERPROFILE\OneDrive\Desktop\Crown2026\frontend\dashboards"
npm install
npx vite --host 127.0.0.1 --port 3000
```

---

## Quick Proof (3 commands, <30 seconds)

```powershell
# Health
Invoke-RestMethod http://127.0.0.1:8000/api/health/

# Demo token
$r = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/dev/token/ -Method POST `
  -ContentType "application/json" -Headers @{"X-Demo-Key"="CrownDemoKey!2026"} `
  -Body '{"persona":"STAFF"}'
$token = $r.access

# Academics sections (key endpoint)
Invoke-RestMethod http://127.0.0.1:8000/api/academics/sections/ `
  -Headers @{"Authorization"="Bearer $token"}
```

Expected: health → `{"status":"ok"}`, token → JWT, sections → 2 results (ENG-101, MATH-101).

---

## Demo Narrative (~5 minutes)

### Scene 1: Home Dashboard (30s)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `http://127.0.0.1:3000/` | Home dashboard loads |
| 2 | Click **Demo Login** button | JWT minted, page refreshes with auth |
| 3 | Point out module cards | Billing, Admissions, Academics, Finance visible |

**If broken:** Verify backend is running (`Invoke-RestMethod http://127.0.0.1:8000/api/health/`).

---

### Scene 2: Teacher Grading (90s)

| Persona | Route |
|---------|-------|
| STAFF | `/academics/teacher-grading` |

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to Teacher Grading | Page loads with section picker |
| 2 | Select **ENG-101** section | Assignments dropdown populates |
| 3 | Select any assignment | Submissions table loads with student names |
| 4 | Click **Status Filter → Submitted** | Table filters to submitted-only rows |
| 5 | Open **Demo Tools** accordion | "Auto-fill 100 for Submitted" button visible |
| 6 | Click **Auto-fill 100** | All submitted rows show score = 100 |
| 7 | Click **Grade** on one row | Score persists, status changes to Graded |

**Talking points:** Real-time grading, per-assignment view, status workflow.

**If broken:** Check `Invoke-RestMethod http://127.0.0.1:8000/api/academics/sections/ -Headers @{"Authorization"="Bearer $token"}` returns data.

---

### Scene 3: Student Work (60s)

| Persona | Route |
|---------|-------|
| STAFF (as student) | `/academics/student-work` |

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to Student Work | Page loads, student picker auto-selects first student |
| 2 | Switch student in dropdown | Tables refresh for selected student |
| 3 | Point out Assignments table | Shows assignment name, status chip, score |
| 4 | Point out Mastery table | Shows objective, mastery level, last assessed |

**Talking points:** Student-centric view, cross-assignment visibility, mastery tracking.

**If broken:** Check `Invoke-RestMethod http://127.0.0.1:8000/api/academics/parents/me/students/ -Headers @{"Authorization"="Bearer $token"}` returns 25 students.

---

### Scene 4: Parent Snapshot (60s)

| Persona | Route |
|---------|-------|
| STAFF (as parent) | `/academics/parent-snapshot` |

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to Parent Snapshot | Page loads with child picker |
| 2 | Select a child | Alerts + transcript load |
| 3 | Point out Missing/Late alert count | Red/orange alert badges with counts |
| 4 | Point out Missing Assignments table | Capped at 8 rows, shows assignment + due date |
| 5 | Scroll to Transcript Preview | Shows course, grade, credits |

**Talking points:** Parent-facing view, proactive alerts, transcript transparency.

**If broken:** Same student endpoint check as Scene 3.

---

### Scene 5: Billing & Finance (60s)

| Persona | Route |
|---------|-------|
| STAFF | `/billing` then `/finance/invoices` |

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to Billing | Dashboard loads with summary |
| 2 | Navigate to Finance Invoices | Invoice list renders |

**Talking points:** Double-entry journal, AR→GL integration, tenant-scoped ledger.

**If broken:** Check `/api/health/` and token are valid.

---

## Post-Demo Cleanup

```powershell
# Kill servers
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process -Name "node" -ErrorAction SilentlyContinue |
  Stop-Process -Force -ErrorAction SilentlyContinue
```
