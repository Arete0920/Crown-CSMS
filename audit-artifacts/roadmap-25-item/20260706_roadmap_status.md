# CROWN 25-Item Roadmap Status — 2026-07-06

**Branch:** `copilot/tcmegahan-crown2026-25-item-roadmap`
**PR closes:** tcmegahan/Crown2026#1244
**Reference PR:** tcmegahan/Crown2026#1237
**Evidence generated:** 2026-07-06

---

## Summary

This document records the current status of each roadmap item in issue #1244,
with classification, evidence references, and next action.

Release posture remains **NO-GO / HOLD** until Lane A settlement is complete.

---

## Lane A — Same-SHA runtime settlement

### Item 1 — Settle PR #1237 on the current head

| Field | Value |
|---|---|
| Status | **IN PROGRESS / NOT SETTLED** |
| PR head SHA | `ba57411d371f507a8d004b11e4b500078074d4cd` |
| merge ref SHA | `fab1f2b94e4c229808493f2a08952c753be813b5` |
| Failing check | Production Certification Evidence |
| Failure classification | **ENVIRONMENT BLOCKER** — stale Azure deployment |

**Evidence:**
CI run for job `85283782806` on head `ba57411d371f507a8d004b11e4b500078074d4cd`:

```
Error: API_SHA_MISMATCH expected=fab1f2b94e4c229808493f2a08952c753be813b5 actual=617a0c4
FRONTEND_SHA_MISMATCH expected=fab1f2b94e4c229808493f2a08952c753be813b5 actual=617a0c48e2800f8cb6eaa4bf0b1d0792b2b6293a
```

The deployed Azure API and frontend are at `617a0c4...` (an earlier deployment),
not the current PR merge head. The `production-runtime-preflight.spec.ts` guard
correctly detected and reported this before running route crawls.

**Next action:** Azure must be redeployed with the current PR code before
same-SHA evidence can pass. This is a deployment environment action, not a
source code fix.

**Checks passing on current head:**
- backend-gates ✅
- pytest-gate ✅
- Sandbox Ready Evidence ✅
- tenant-tests ✅
- frontend build/lint ✅
- schema-governance ✅
- dashboard-ui-gates ✅
- CodeQL, gitleaks, secret-scan ✅
- 65+ other checks ✅

**Checks failing on current head:**
- Production Certification Evidence ❌ (Azure stale — environment blocker)

### Item 2 — Confirm deployed dashboard bundle contains current fixes

| Status | **BLOCKED on Item 1** |
|---|---|
| Dependency | Azure deployment must advance to current PR head |

### Item 3 — Verify live persona auth truth in production runtime

| Status | **BLOCKED on Item 1** |
|---|---|
| Dependency | Azure deployment must advance to current PR head |

### Item 4 — Re-run Production Certification Evidence on settled SHA

| Status | **BLOCKED on Item 1** |
|---|---|
| Note | Certification preflight guard is in place and working correctly |

### Item 5 — Update release authority only if refreshed same-SHA evidence supports it

| Status | **BLOCKED on Items 1–4** |
|---|---|
| Note | Authority docs must not be updated until Items 1–4 pass |

---

## Lane B — Sandbox/auth authority

### Item 6 — Record environment decision for CROWN_SANDBOX_ALLOW_OPEN_SESSION

| Status | PENDING — governance decision required |
|---|---|
| Note | Variable is present in env config; explicit tier-by-tier decision not yet documented |

### Item 19 — Deterministic no-login sandbox proof authority

| Status | PENDING — governance decision required |
|---|---|
| Note | No-login Heritage sandbox path is in place; authority/retirement decision not made |

### Item 20 — Remove demo passwords from repo surfaces

| Status | PENDING — depends on Item 19 decision |
|---|---|
| Note | Must not be executed before Item 19 is decided |

---

## Lane C — Operational proof

### Items 7–12 — Operational proof gates

| Status | ALL BLOCKED on Lane A settlement |
|---|---|
| Note | No operational proof run is current against the decision SHA |

---

## Lane D — Pilot/business readiness

### Items 13–16 — Pilot and compliance readiness

| Status | ALL PENDING — no school selected, no DPA executed |
|---|---|
| Note | Must not begin until Lane A is settled |

---

## Lane E — Cleanup/governance/diligence

### Item 17 — Finish remaining root cleanup lane

| Status | PARTIAL — PR #1238 merged connector-safe root hygiene |
|---|---|
| Evidence | `audit-artifacts/repo-hygiene/20260702_connector_safe_cleanup.md` |

### Item 18 — Execute evidence slimming

| Status | PENDING |

### Item 21 — Remove nested duplicate sandbox_demo tree

| Status | PENDING — duplicate confirmed but byte-identical check not yet committed |

### Item 22 — Disposition of docs/investor-audit under public-repo threat model

| Status | PENDING — governance decision required |

### Item 23 — Expand coverage truth reporting

| Status | PENDING |

### Item 24 — Fix random-UUID parametrization issue blocking pytest-xdist

| Status | **FIXED — committed in this PR** |
|---|---|
| Files changed | `backend/financial_aid/tests/test_auth_smoke.py` |
| | `backend/financial_aid/tests/test_url_routes.py` |
| Change | `BILLING_RUN_ID = str(uuid.uuid4())` → `BILLING_RUN_ID = "11111111-1111-4111-8111-111111111111"` |
| Validation | 6/6 parametrized tests pass locally |

**Root cause:** Both test files computed `BILLING_RUN_ID` at module import time using
`uuid.uuid4()`. When `pytest-xdist` distributes tests, each worker re-imports
the module and gets a different UUID. The collected test node IDs (from the
coordinator process) no longer match the worker process IDs, so distributed
test runs fail to find the correct test cases.

**Fix:** Replace with a fixed deterministic UUID string that is valid for the
URL pattern but never changes between process imports. The UUID value is
irrelevant to the test assertion — only the URL pattern match matters.

### Item 25 — Burn down schema and bundle debt

| Status | PARTIAL / IN PROGRESS |
|---|---|
| Note | drf-spectacular warns on ~60 APIViews lacking explicit serializer_class. Addressed as a separate lane. |

---

## Overall Release Posture

**NO-GO / HOLD**

The release posture may not change until:
1. Lane A Item 1 is settled (Azure deployed to current PR head)
2. Items 2–5 pass on the settled SHA
3. Independent review is complete

AI assistants cannot approve their own work. Use `INDEPENDENT_REVIEW_REQUIRED`
until a human reviewer has completed review.
