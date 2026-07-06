# CROWN Release Execution Order - May 1, 2026

**Authoritative Artifact Folder:** `audit-artifacts/judgment-day-gauntlet/20260430_212943/`

**Current Status:** 🟢 GO (all non-Azure P0-3 complete, P0-4 through P1-3 ready)  
**Blockers:** Azure deployment (5 teams waiting)

---

## ⚡ IMMEDIATE EXECUTION ORDER

### 1️⃣ DEV 1 / DEV 2 / DEV 5: Runtime Proof Execution

**Start File:** `audit-artifacts/judgment-day-gauntlet/20260430_212943/60b_RUNTIME_PROOF_EXECUTION_GUIDE.md`

**Focus First (Complete within 2 hours):**
- **TI-001 through TI-007**: Tenant isolation proofs
  - TI-001: School A admin cannot access School B student
  - TI-002: School A parent cannot access School B household
  - TI-003: School A finance cannot access School B billing
  - TI-004: School A teacher cannot access School B roster/grades
  - TI-005: School A dashboard does not aggregate School B
  - TI-006: Cross-tenant API calls blocked (tenant_id mismatch)
  - TI-007: Token validation isolates by school_id

- **RBAC-001 through RBAC-002**: Core role-access proofs
  - RBAC-001: Parent cannot access admin dashboard
  - RBAC-002: Teacher cannot access finance billing

**Then Execute (Next 2-3 hours):**
- RBAC-003 through RBAC-006 (remaining role isolation)
- WF-001 through WF-006 (workflow proofs with Dev 3 if available)

**Evidence Output:** Update `60_required_runtime_proof_matrix.csv` with Pass/Fail for each proof

**Success Criteria:** All TI-001-007 and RBAC-001-002 = PASS

---

### 2️⃣ DEV 4: UI Polish & Dashboard Review

**Start File:** `audit-artifacts/judgment-day-gauntlet/20260430_212943/P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md`

**Complete in parallel with Runtime Proofs (2-3 hours):**
- Fix dead links (`href="#"` patterns)
- Remove or implement TODO/FIXME UI elements
- Verify dashboard pages:
  - Home Dashboard: KPI tiles, drill-downs, data accuracy
  - Teacher Dashboard: Roster view, attendance posting, navigation
  - Parent Dashboard: Household/student selection, billing section
  - Student Dashboard: Schedule, grades, attendance
- Verify canonical routing (no 404s on expected paths)

**Testing Checklist:**
```
[ ] Dashboard pages load without 404s
[ ] All links navigate to valid pages
[ ] No dead links or href="#" in production pages
[ ] KPI tiles show correct data
[ ] Drill-downs navigate to source detail pages
[ ] Mobile and desktop views match design
```

**Evidence Output:** Screenshot verification + test runs in `P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md`

**Success Criteria:** All action plan items marked COMPLETE

---

### 3️⃣ AZURE TEAM: Prepare for Go-Live

**Start File:** `audit-artifacts/judgment-day-gauntlet/20260430_212943/P7_POST_AZURE_FINAL_PROOF_PACKET.md`

**Use immediately when Azure setup is complete:**

**Pre-Deployment (RIGHT NOW - prepare checklist):**
1. Verify RBAC role assignments
2. Verify managed identity permissions
3. Verify App Service connection strings / Key Vault refs
4. Verify database migrations and indexes

**Post-Deployment (when Azure resources are live):**
1. ✅ Health endpoint responds (HTTP 200)
2. ✅ Database connectivity verified
3. ✅ Authentication flow works (can log in)
4. ✅ Authorization boundaries enforced (cross-school access blocked)
5. ✅ Performance meets baseline (< 200ms response time)
6. ✅ Data isolation verified (School A cannot see School B)

**Success Criteria:** All 6 gates = PASS

---

### 4️⃣ AFTER AZURE PROOF PASSES: Final Judgment Day Re-run

**When:** Immediately after P7 post-Azure validation passes  
**Command:**
```powershell
$env:CROWN_VALIDATION_TIMEOUT_SEC="420"
$env:CROWN_LOAD_REQUESTS="100"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
& "C:\w\crown_main_postmerge_verify\scripts\execution\crown_judgment_day_gauntlet.ps1"
```

**Output:** New scorecard with Judgment Day Score (target: 500+ / 1000, up from 411)

**Decision:**
- Score 500+: **GO** → Ready for production
- Score 400-500: **RELEASE_CANDIDATE** → Additional validation needed
- Score < 400: **NO-GO** → Escalate

---

## 📊 Current Status Snapshot

| Phase | Status | Owner | Evidence |
|-------|--------|-------|----------|
| **P0-1: Repo Hygiene** | ✅ COMPLETE | Done | Commit abf5449 |
| **P0-2: Security Triage** | ✅ COMPLETE | Done | 22b_security_triage_report.md (567→0 real secrets) |
| **P0-3: Tenant Isolation (Code Review)** | ✅ COMPLETE | Done | 24b_tenant_isolation_triage_report.md (201→0 bypasses) |
| **P0-4: Runtime Proofs (Execution)** | 🔄 IN PROGRESS | Dev 1/2/5 | 60b_RUNTIME_PROOF_EXECUTION_GUIDE.md |
| **P1-1: UI Polish** | 🔄 IN PROGRESS | Dev 4 | P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md |
| **P7: Post-Azure Validation** | ⏳ PENDING | Azure + Dev 5 | P7_POST_AZURE_FINAL_PROOF_PACKET.md |
| **Final Gauntlet Re-run** | ⏳ PENDING | Dev 5 | New scorecard output |

---

## 🎯 Release Blocker Pyramid (Current)

```
Level 1: Azure Deployment Completion  ← BLOCKING all teams
  │
Level 2: Runtime Proof Execution     ← Dev 1/2/5 working NOW
  ├─ TI-001-007 (tenant isolation)
  └─ RBAC-001-006 (role access)
  │
Level 3: UI Polish & Route Review    ← Dev 4 working NOW
  │
Level 4: Post-Azure Gates (6 gates)  ← Ready to execute when Azure done
  │
Level 5: Final Gauntlet Score        ← Final decision gate
```

**Timeline:**
- Runtime Proofs: 4-6 hours (parallel with UI polish)
- UI Polish: 2-3 hours (parallel)
- Azure Setup: TBD (5 teams waiting)
- Post-Azure Validation: 1 hour
- Gauntlet Re-run: 15-20 minutes

**Unblock Path:** Runtime proofs + UI polish = 6 hours → Azure team gets green light

---

## 📁 Key Artifact Files (Reference)

| File | Purpose | Start Here |
|------|---------|-----------|
| `README_SESSION_HANDOFF.txt` | Session overview | For context |
| `SESSION_COMPLETION_SUMMARY.md` | Work completed | Status snapshot |
| `60b_RUNTIME_PROOF_EXECUTION_GUIDE.md` | **Runtime proof details + curl commands** | **Dev 1/2/5** |
| `P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md` | **UI polish checklist** | **Dev 4** |
| `P7_POST_AZURE_FINAL_PROOF_PACKET.md` | **Post-Azure validation gates** | **Azure team** |
| `80_JUDGMENT_DAY_SCORECARD.csv` | Current scorecard (411/1000) | Reference |
| `81_JUDGMENT_DAY_BLOCKER_BOARD.csv` | P0-1 status tracking | Reference |

---

## ✅ Team Assignments

```
Dev 1:  TI-001, TI-004, RBAC-001, RBAC-003, WF-001
Dev 2:  TI-002, TI-004, WF-001, WF-004
Dev 3:  WF-003 (billing workflows)
Dev 4:  P1 UI Polish + TI-005 (dashboard KPIs) + UI-001-003
Dev 5:  TI-003, TI-006-007, RBAC tests, coordinate post-Azure validation
Azure:  Deployment execution → triggers P7 validation
```

---

## 🚀 Next Immediate Actions

**Right Now (Next 30 minutes):**
1. ✅ This document sent to all teams
2. ✅ Dev 1/2/5: Open `60b_RUNTIME_PROOF_EXECUTION_GUIDE.md`
3. ✅ Dev 4: Open `P1_UI_DASHBOARD_ROUTE_ACTION_PLAN.md`
4. ✅ Azure team: Bookmark `P7_POST_AZURE_FINAL_PROOF_PACKET.md`

**Next 2 hours:**
- Dev 1/2/5: Execute TI-001-007 + RBAC-001-002 tests
- Dev 4: Start UI polish checklist
- Azure team: Prepare pre-deployment checklist (P7 step 1)

**Success = Unblock Azure team:**
- Runtime proofs all PASS
- UI polish all COMPLETE
- Azure team proceeds with deployment
- We execute post-Azure gates
- New scorecard determines final decision

---

**Authority:** Generated from `audit-artifacts/judgment-day-gauntlet/20260430_212943/`  
**Last Updated:** 2026-05-01 01:47 UTC  
**Owner:** Release Engineering
