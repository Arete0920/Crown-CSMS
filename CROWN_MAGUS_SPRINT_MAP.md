# CrownMagus0 – Dev Sprint Map + Gate 4 Lock Checklist

**Objective:** Move from "demo-capable" → "production-hardened"  
**Duration:** 4 Sprints × 2 weeks = 8 weeks to Gate 4 Lock  
**Tag target:** `crown-0.4.0-gate4-locked`

---

## Engineer Roles

| Engineer | Domain | Profile |
|----------|--------|---------|
| E1 | Metrics & Aggregation Lead | Strong ORM + data modeling |
| E2 | Financial Integrity Lead | Ledger + invariants specialist |
| E3 | Wizard & Workflow Engineer | React + multi-step flows |
| E4 | Governance & Reporting Lead | Analytics + PDF generation |
| E5 | Academics Engine Lead | GPA, transcripts, rules |
| E6 | DevOps & Security Lead | CI/CD + auth + hardening |

---

## Sprint 1 — Metrics Reality Pass

**Goal:** Replace all stub dashboards with real aggregation logic.

**Modules in scope:** Admissions · Financial Aid · Attendance · Discipline · Spiritual Life

### Required Deliverables

#### 1. Replace Stub Endpoints

Every endpoint must:
- Use tenant-scoped queryset
- Use annotated aggregation
- Be tested for cross-tenant bleed

**Standard pattern:**
```python
school_id = get_request_school_id(request, required=True)
qs = Application.objects.filter(school_id=school_id)
return Response({
    "total": qs.count(),
    "approved": qs.filter(status="approved").count(),
    "pending": qs.filter(status="pending").count(),
})
```

#### 2. Metrics Contract Tests

Each metrics endpoint must have:
```python
def test_metrics_are_tenant_isolated(client, school_a, school_b):
    ...
```

#### 3. Financial Aid Drilldown Endpoint

`/api/v1/financial-aid/drilldown/?bucket=Need-Based`

Must:
- Validate bucket
- Aggregate by student
- Return paginated detail
- Enforce tenant scope

### Sprint 1 Task List

| # | Title | Owner | Gate Critical | Tenant Required |
|---|-------|-------|:---:|:---:|
| 1 | Replace Admissions Metrics Stub | E1 | ✅ | ✅ |
| 2 | Implement Financial Aid Drilldown Endpoint | E1 | ✅ | ✅ |
| 3 | Replace Attendance Metrics Stub | E1 | | ✅ |
| 4 | Replace Discipline Metrics Stub | E1 | | ✅ |
| 5 | Replace Spiritual Metrics Stub | E1 | | ✅ |
| 6 | Frontend Drilldown Drawer Integration | E3 | | |
| 7 | Metrics Contract Tests Suite | E1 | ✅ | |
| 8 | CI Integration – Metrics Enforcement | E6 | | |

### Sprint 1 Exit Criteria

| Item | Must Be |
|------|---------|
| All metrics live | ✅ |
| No stub data | ✅ |
| All metrics tenant-tested | ✅ |
| CI passing | ✅ |

---

## Sprint 2 — Financial Integrity Hardening

**Goal:** Make ledger invariant-proof.

**In scope:** FIFO allocation · Void/reversal · Audit logging · Tuition Plan Wizard

### Required Deliverables

#### 1. Ledger Invariant Tests

Must fail if:
- Allocation exceeds payment
- Void does not rebalance
- School cross-tenant leakage

```python
def test_fifo_allocation_does_not_over_allocate():
    ...

def test_void_creates_balancing_entry():
    ...
```

#### 2. Audit Log Enforcement

All financial mutations must:
- Write `AuditEntry`
- Include `user_id`
- Include `school_id`
- Include `timestamp`

No silent mutations.

#### 3. TuitionPlanWizard Build

**Wizard steps:**
1. Plan Name
2. Installment Count
3. Due Schedule
4. Fee Mapping
5. Review + Save

Must:
- Validate installment math
- Prevent negative totals
- Enforce tenant scope

### Sprint 2 Task List

| # | Title | Owner | Priority | Gate Critical | Financial Impact |
|---|-------|-------|----------|:---:|:---:|
| 9 | Implement FIFO Invariant Tests | E2 | Critical | ✅ | ✅ |
| 10 | Enforce Double-Entry Void Logic | E2 | Critical | ✅ | ✅ |
| 11 | Audit Log Completion – All Financial Mutations | E2 | Critical | ✅ | ✅ |
| 12 | Build TuitionPlanWizard Backend | E2 | High | | |
| 13 | Build TuitionPlanWizard Frontend (5-Step) | E3 | High | | |
| 14 | Enable Strict Financial Test Gate in CI | E6 | High | ✅ | |

### Sprint 2 Exit Criteria

| Item | Must Be |
|------|---------|
| Ledger invariant tested | ✅ |
| Void idempotent | ✅ |
| Audit logging complete | ✅ |
| Tuition plan wizard operational | ✅ |

---

## Sprint 3 — Governance + Board Layer

**Goal:** Board-ready system intelligence.

**In scope:** Crown Compass scoring · Board metrics endpoint · Board pack generator · KPI categorization

### Required Deliverables

#### 1. Crown Compass Scoring Engine

**Scoring domains:**

| Domain | Weight |
|--------|--------|
| Enrollment Health | 20% |
| Financial Stability | 25% |
| Academic Performance | 20% |
| Discipline Health | 10% |
| Spiritual Formation | 15% |
| Retention | 10% |

**Response shape:**
```json
{
  "overall_score": 82,
  "domains": {
    "finance": 88,
    "enrollment": 74,
    "academics": 79,
    "discipline": 85,
    "spiritual": 80,
    "retention": 90
  }
}
```

#### 2. Board Metrics Endpoint

`/api/v1/board/metrics/`

Must aggregate:
- Enrollment trend
- Aid budget usage
- Net tuition revenue
- Attendance rate
- Discipline rate
- Retention %

#### 3. Board Pack Generator

- Generate PDF summary
- Include KPI graphs
- Include Crown Compass score
- School-branded

### Sprint 3 Task List

| # | Title | Owner | Gate Critical |
|---|-------|-------|:---:|
| 15 | Build Crown Compass Scoring Engine | E4 | ✅ |
| 16 | Implement Board Metrics Aggregation Endpoint | E4 | ✅ |
| 17 | Implement Weighted KPI Engine | E4 | |
| 18 | Build Board PDF Export Engine | E4 | ✅ |
| 19 | Ensure Shared Aggregation Logic Reuse | E1 | |

### Sprint 3 Exit Criteria

| Item | Must Be |
|------|---------|
| Compass scoring deterministic | ✅ |
| Board dashboard live | ✅ |
| Board PDF export working | ✅ |

---

## Sprint 4 — Academics Completion

**Goal:** Close the academic loop.

**In scope:** Transcript engine · Promotion rule enforcement · Bulk grade entry · GPA calculation

### Required Deliverables

#### 1. Transcript Engine

`/api/v1/transcripts/{student_id}/`

Must:
- Pull completed courses
- Compute GPA
- Show credits earned
- Generate PDF

#### 2. Promotion Rule Engine

Rules enforced:
- Minimum GPA
- Required credits
- Attendance threshold

Fails promotion if any rule unmet.

### Sprint 4 Task List

| # | Title | Owner | Gate Critical |
|---|-------|-------|:---:|
| 20 | Implement GPA Calculation Engine | E5 | ✅ |
| 21 | Build Transcript Generation Endpoint | E5 | |
| 22 | Transcript PDF Export | E5 | |
| 23 | Implement Promotion Rule Engine | E5 | ✅ |
| 24 | Build Bulk Grade Entry UI | E3 | |
| 25 | Tenant Enforcement Audit for Academics | E6 | ✅ |

### Sprint 4 Exit Criteria

| Item | Must Be |
|------|---------|
| Transcript generation stable | ✅ |
| Promotion rule enforced | ✅ |
| GPA accurate | ✅ |

---

## Gate 4 Lock Checklist

> Non-negotiable. No "close enough."

### Auth & Tenant Lock

- [ ] All endpoints require JWT
- [ ] All endpoints enforce `school_id`
- [ ] No raw `.objects.get()` without tenant filter
- [ ] `verify_backend_gate.py` passes
- [ ] CI strict-mode enabled

**Owner: E6**

### Financial Lock

- [ ] All ledger mutations audited
- [ ] FIFO invariant tested
- [ ] Void idempotent
- [ ] Payment cannot exceed charge
- [ ] Cross-tenant financial bleed impossible

**Owner: E2**

### Metrics Lock

- [ ] No stub endpoints
- [ ] All metrics tenant-scoped
- [ ] All metrics tested
- [ ] Drilldowns validated

**Owner: E1**

### Wizard Lock

Every wizard must:
- [ ] Persist state
- [ ] Validate inputs
- [ ] Enforce tenant
- [ ] Have test coverage
- [ ] Fail gracefully

**Owner: E3**

### Governance Lock

- [ ] Crown Compass deterministic
- [ ] Board dashboard stable
- [ ] PDF pack export works
- [ ] KPI definitions documented

**Owner: E4**

### Deployment Lock

- [ ] Health endpoint returns `BUILD_SHA`
- [ ] No `DEBUG=True`
- [ ] CORS restricted
- [ ] Demo mode disabled in prod
- [ ] Audit logging enabled
- [ ] Secrets rotated

**Owner: E6**

---

## Gate Lock Task List (Tasks 26–32)

| # | Title | Owner | Gate Critical |
|---|-------|-------|:---:|
| 26 | Enforce JWT Across All Endpoints | E6 | ✅ |
| 27 | Enforce `school_id` on All Querysets | E6 | ✅ |
| 28 | Disable Demo Mode in Production | E6 | ✅ |
| 29 | CORS Restriction for Production | E6 | ✅ |
| 30 | Enable Audit Logging Globally | E6 | ✅ |
| 31 | Add `BUILD_SHA` to Health Endpoint | E6 | ✅ |
| 32 | Full Regression Test Pass | All | ✅ |

---

## Engineer Gate Signoffs

| Engineer | Domain | Must Certify |
|----------|--------|-------------|
| E6 — Gate Lock Authority | DevOps | JWT · Tenant · CORS · Demo off · DEBUG off · BUILD_SHA · CI strict |
| E2 — Financial Signoff | Ledger | Invariants · Void balancing · Audit logging · No silent mutations |
| E4 — Governance Signoff | Board | Compass deterministic · Board metrics accurate · PDF stable |
| E5 — Academic Signoff | Academics | GPA correct · Transcript accurate · Promotion rule enforced |
| E1 — Data Integrity Signoff | Metrics | All metrics tenant-scoped · No stubs · No duplicate aggregation |
| E3 — Wizard Integrity Signoff | Wizards | Step validation · Tenant enforcement · Test coverage · Graceful failure |

> E6 has veto authority on tag release. No tag without E6 signoff.

---

## Parallel Execution Structure

| Sprint | Parallel Tracks |
|--------|----------------|
| 1 | Metrics (E1) + Frontend integration (E3) + CI (E6) |
| 2 | Financial core (E2) + Wizard UI (E3) + CI gate (E6) |
| 3 | Governance engine (E4) + Aggregation support (E1) |
| 4 | Academics (E5) + Bulk entry UI (E3) + Hardening (E6) |

Each sprint ends with: CI freeze · Review branch · Tag checkpoint

---

## Risk Control Structure

| Domain | Risk if Slips | Level |
|--------|--------------|-------|
| Financial | Legal liability | 🔴 Critical |
| DevOps | System-wide | 🔴 Critical |
| Metrics | Demo credibility | 🟡 High |
| Governance | Investor credibility | 🟡 High |
| Academics | School operations | 🟡 High |

---

## Final Certification Requirement

Before tagging `crown-0.4.0-gate4-locked`, run and archive:

```powershell
pytest
python verify_backend_gate.py
gh pr checks
ci_runtime_canary
```

Archive:
- HEAD SHA
- Health endpoint output (`/api/health/` + `/api/integrity/`)
- Full test output
- Proof log

---

## Scalability Context

| School Count | Risk Profile |
|-------------|-------------|
| 25 | Manageable — demo-grade acceptable |
| 150 | This structure becomes mandatory |
| 400 | Without this structure, collapse risk rises sharply |
