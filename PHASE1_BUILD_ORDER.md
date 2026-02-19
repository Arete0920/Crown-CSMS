# PHASE 1 BUILD ORDER (Authoritative) — Crown2026
Prepared by: John T.C. Megahan
Date: 2026-02-19 (rolling; update only via PR)

## Objective (Deadline: 2026-03-30)
Deliver an operational, pilot-credible Crown platform with:
- Admissions→Enrollment→Student record
- Tuition→Invoices→Payments→Balance
- Teacher Attendance (persisted + visible)
- Teacher Gradebook (persisted + parent-visible)
- Parent Portal (My Student: attendance, grades, balance, graduation)
- Uniform Auth + X-School-Id + RBAC enforcement on all Phase 1 APIs
- Proof scripts + CI gate + tagged releases

## Non-negotiable rules
1) Spec BEFORE code: every change must list files/endpoints/routes + acceptance checks.
2) One lane at a time. No jumping.
3) No refactors unless required to pass acceptance.
4) Fail fast: if any acceptance fails, stop and fix root cause.
5) CI gate is authoritative: Phase 1 gate must pass for merge.

## Lanes (Execute in order)

### Lane 1 — Admissions→Enrollment→Student Record
**Goal:** admin can enroll a student and see them in roster + Student360.
**Acceptance:**
- API: enroll action returns 200/201 and student appears in roster endpoint.
- UI: admin can click Enroll (or equivalent) and student appears in Student360 page.

**Artifacts required (exact):**
- Endpoint(s): /api/... admissions/enroll or equivalent
- UI route(s): existing Admissions page + Student360
- Seed: deterministic demo student(s)

### Lane 2 — Tuition→Invoices→Payments→Balance
**Goal:** money loop works and is visible.
**Acceptance:**
- Invoice list shows generated invoices
- Payment posting updates balance immediately
- Export works (if present)

### Lane 3 — Teacher Attendance Workflow
**Goal:** teacher submits attendance and it is visible to admin + parent.
**Acceptance:**
- Teacher can mark attendance for a class section for today
- Attendance persists in DB
- Parent view reads it

### Lane 4 — Teacher Gradebook Workflow
**Goal:** teacher enters grade and parent sees it.
**Acceptance:**
- Teacher enters score for assignment
- Average updates
- Parent sees grade list/average

### Lane 5 — Parent Portal Consolidation
**Goal:** parent has a coherent entry point, not just URLs.
**Acceptance:**
- Parent landing contains "My Student"
- My Student shows Attendance, Grades, Balance/Invoices, Graduation

### Lane 6 — Security sweep (Phase 1 APIs only)
**Goal:** no Phase 1 endpoint works without Authorization + X-School-Id, and RBAC is correct.
**Acceptance:**
- Every Phase 1 endpoint returns 401/403 if missing auth/context
- Correct roles can read/write; incorrect roles denied

### Lane 7 — Ops Proof + Release Tag
**Goal:** repeatable proof on demand.
**Acceptance:**
- scripts/phase1/phase1_proof.ps1 passes locally
- phase1-gate.yml passes in CI on PR
- Tag created for release checkpoints

## Definition of DONE for Phase 1 (2026-03-30)
DONE means:
- Lanes 1–7 all pass, repeatedly, on a fresh seed.
- No demo-only bypass in production mode.
- CI gate green.
- Release tag exists and matches proof output.
