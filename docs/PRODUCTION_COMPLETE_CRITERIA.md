# Crown2026 — Production Complete Criteria

> **Purpose:** A single-page authority for what "production complete" means. Each criterion maps to evidence. This is the owner/investor handoff checklist.

**Frozen baseline:** `prod-proof-baseline-2026-02-24` → `d917c9865348fe2835fe5ee0e1da06eb85710f87`

---

## 1. Deploy Integrity

| Check | Status | Evidence |
|---|---|---|
| Tag-driven deploy (no manual push to prod) | PASS | `prod-deploy-2026-02-24-0545` triggered `deploy-prod.yml` |
| BUILD_SHA guard (workflow step) | PASS | Run [#22347445277](https://github.com/tcmegahan/Crown2026/actions/runs/22347445277) — step "Guard: verify BUILD_SHA app setting matches deployed SHA" ✅ |
| Azure `BUILD_SHA` app setting matches deployed SHA | PASS | `d917c9865348fe2835fe5ee0e1da06eb85710f87` in Azure + `/api/health/` |
| `/api/health/` returns `ok: true` | PASS | `{"ok":true,"status":"ok","build_sha":"d917c986...","prod_deploy_tag":"prod-deploy-2026-02-24-0545","env":"prod","db":"ok"}` |
| `ENVIRONMENT=prod` | PASS | Azure app setting confirmed |
| `DEBUG=False` | PASS | Azure app setting confirmed |
| `DEMO_MODE=off` | PASS | `/api/health/` → `"demo_mode": false` |

---

## 2. Security & Secrets Hygiene

| Check | Status | Evidence |
|---|---|---|
| gitleaks clean (full history) | PASS | `exit: 0, 1252 commits, 0 findings` — see [PROOF_LOG_2026-02-24.md](PROOF_LOG_2026-02-24.md) |
| No `AllowAny` overrides on API views | PASS | PR #400 merged — all ViewSets use `IsAuthenticated` baseline |
| CORS locked to prod origin only | PASS | `CORS_ALLOWED_ORIGINS=https://crown-api-prod.azurewebsites.net` |
| No secrets in tracked files | PASS | gitleaks scan — 0 findings on current HEAD |
| Branch protection: main requires PR + status checks | PASS | Squash-only merges enforced; see `branch_protection.json` |

---

## 3. Tenant Enforcement

| Check | Status | Evidence |
|---|---|---|
| All API requests require `X-School-ID` header (or JWT tenant) | PASS | `test_tenant_header_required.py` — 4 tests PASS |
| Context guardrails restore after request | PASS | `test_tenant_context_guardrails.py` — 3 tests PASS |
| Cross-tenant write blocked | PASS | `test_tenant_write_guard.py` — 2 tests PASS |
| JWT tenant cannot be overridden by header | PASS | `test_tenant_enforcement.py::test_cross_tenant_header_does_not_override_jwt_tenant` PASS |
| Proof command (38/38) | PASS | See [PROOF_LOG_2026-02-24.md](PROOF_LOG_2026-02-24.md) |

---

## 4. RBAC Contract

| Check | Status | Evidence |
|---|---|---|
| Role matrix: FINANCE_DIRECTOR → 200, HEAD_OF_SCHOOL → 200, TEACHER/PARENT/STUDENT → 403 | PASS | `test_rbac_contract.py` — 7 tests PASS |
| Unauthenticated requests → 401 | PASS | `test_rbac_contract.py::test_requires_auth_for_invariants` PASS |
| Missing tenant header → 400 | PASS | `test_rbac_contract.py::test_requires_tenant_header_for_invariants` PASS |
| Finance proof: forbidden without role | PASS | `test_rbac_proof.py` — 3 tests PASS |

---

## 5. Ledger Invariants

| Check | Status | Evidence |
|---|---|---|
| Over-allocation detected | PASS | `test_ledger_invariants.py::test_invariants_detects_over_allocation` PASS |
| Tenant isolation at ledger level | PASS | `test_ledger_invariants.py::test_invariants_tenant_isolation` PASS |
| Charge amount immutable after creation | PASS | `test_ledger_immutability.py` — 6 tests PASS |
| Negative/zero charges rejected | PASS | `test_ledger_write_safety.py` — 5 tests PASS |
| Over-allocation payment rejected | PASS | `test_ledger_write_safety.py::test_record_payment_rejects_over_allocation` PASS |

---

## 6. Core Workflow Completeness

| Module | API | Tests | Status |
|---|---|---|---|
| Admissions | ✅ | ✅ | Complete |
| Financial Aid / Awards | ✅ | ✅ | Complete (gold standard) |
| Finance / Billing | ✅ | ✅ | Complete |
| Attendance | ✅ | ✅ | Complete |
| Gradebook | ✅ | ✅ | Complete |
| Academics / Roster | ✅ | ✅ | Complete |
| Enrollment | ✅ | ✅ | Complete |
| Ledger | ✅ | ✅ | Complete |
| HR | ✅ | ✅ | Phase 3 merged |
| Advancement | ✅ | ✅ | Phase 3 merged |
| PD Hub | ✅ | ✅ | Phase 3 merged |
| Safety | ✅ | ✅ | Phase 3 merged |
| Director Actions API | ✅ | ✅ | Complete |

**Full suite:** 589 passed · 11 skipped · 0 failed (last full run, Phase 3 merge)

---

## 7. UI Proof

| Check | Status | Notes |
|---|---|---|
| Admin dashboard loads + Quick Actions render | ✅ Manual | HR + Safety added (Phase 3) |
| Teacher attendance submit | ✅ Manual | Gradebook/attendance proof Feb 16 |
| Parent dashboard loads | ✅ Manual | Parent360 proof Feb 16 |
| Playwright automated suite | ❌ Not built | No spec files exist outside node_modules — acceptance criteria for next phase |

**UI blocker:** No automated Playwright specs exist. Manual proof passes. Automated UI proof is the next acceptance gate before investor handoff.

---

## 8. Open Items Before Investor Handoff

| Item | Priority | Owner |
|---|---|---|
| Playwright smoke suite (4 critical paths) | HIGH | Next phase |
| CodeQL code scanning enabled (workflow warning) | MEDIUM | Repo settings |
| CodeQL Action v3 → v4 (deprecates Dec 2026) | LOW | Before Dec 2026 |
| `DEMO_MODE` flag confirmed false in prod health | DONE | `"demo_mode": false` |

---

## Proof Log

See [PROOF_LOG_2026-02-24.md](PROOF_LOG_2026-02-24.md) for raw test output and health response.
