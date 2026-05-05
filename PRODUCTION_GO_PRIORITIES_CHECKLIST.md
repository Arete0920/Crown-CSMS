# Crown Production GO — Priorities Checklist

**Created:** 2026-05-05T19:00 UTC  
**From:** PRODUCTION_READINESS_DECISION_20260505.md  
**Status:** Ready for execution

---

## Phase 1: Unlock Production GO (REQUIRED)

### Priority 1️⃣ — Founder/Product-Owner Final Acceptance

**Timeline:** < 1 hour  
**Owner:** Leadership  
**Status:** ⏳ PENDING

**Steps:**
- [ ] Read PRODUCTION_READINESS_DECISION_20260505.md
- [ ] Review FINAL_PRODUCTION_RELEASE_CERTIFICATION_20260501.md
- [ ] Understand conditional GO-CANDIDATE status
- [ ] Sign off final acceptance (append to certification or create new acceptance artifact)
- [ ] Confirm: "We approve production deployment proceeding under conditional certification"

**Evidence Location:** `FINAL_PRODUCTION_RELEASE_CERTIFICATION_20260501.md` (append)  
**Blocker Resolution:** Once signed, removes HIGH-RISK item from decision matrix

---

### Priority 2️⃣ — Governance Control Re-Proof (Admin-Level GitHub Access)

**Timeline:** < 30 minutes  
**Owner:** Release Engineering (with admin GitHub token)  
**Status:** ⏳ PENDING — Requires admin credentials

**✋ NOTE:** Current integration token lacks admin permissions (403 errors on both queries):
- Rulesets: "Upgrade to GitHub Pro or make this repository public"
- Branch protection: "Resource not accessible by integration"

**Required Action:**
1. **Option A:** Use GitHub CLI with personal admin account:
   ```bash
   # Logout current token
   gh auth logout
   # Login with admin credentials
   gh auth login
   # Run queries
   gh api repos/tcmegahan/Crown2026/rulesets > 06_RULESETS_PROOF_ADMIN.json
   gh api repos/tcmegahan/Crown2026/branches/main/protection > 07_BRANCH_PROTECTION_PROOF_ADMIN.json
   ```

2. **Option B:** Use GitHub web UI with admin account to take screenshots of:
   - Rulesets page: https://github.com/tcmegahan/Crown2026/settings/rules
   - Branch protection page: https://github.com/tcmegahan/Crown2026/settings/branches

**After Obtaining Proof:**
- [ ] Copy outputs to: `audit-artifacts/final-production-release/20260501_153828/`
- [ ] Update `GATE_RESULTS.csv`:
  - Change "Ruleset proof" from FAIL → PASS
  - Change "Branch protection proof" from REVIEW → PASS
- [ ] Commit with message: "docs(release): add admin-level governance control proof (May 5)"

**Evidence Location:** `audit-artifacts/final-production-release/20260501_153828/`  
**Blocker Resolution:** Once complete, removes MEDIUM-RISK governance API gaps

**⚠️ WHO CAN DO THIS:** Only GitHub account owner or repository admin

---

### Priority 3️⃣ — Health-Watch Transient Confirmation

**Timeline:** 1–3 hours (passive observation)  
**Owner:** On-call ops monitoring  
**Status:** ✅ CONFIRMED — Transient glitch resolved

**Verification Results:**
- 2026-05-05T14:00-15:00 UTC: 2 consecutive failures (transient window)
- 2026-05-05T15:45 UTC onwards: **6 consecutive successes** 🟢
- Most recent run: 2026-05-05T19:12:12Z SUCCESS
- **Assessment:** Transient glitch confirmed and resolved. No ongoing operational risk.

**Evidence:** https://github.com/tcmegahan/Crown2026/actions?query=workflow%3A%22Production+Health+Watch%22

**Resolution:** ✅ Health-watch signal is stable. No action required. Cleared for production deployment.

---

## Phase 2: Deploy to Production (After Phase 1 Complete)

### Step 4 — Deploy to Production

**Timeline:** 1–2 hours  
**Owner:** Platform/DevOps  
**Prerequisites:** Phase 1 items 1–3 all complete

- [ ] Pre-deployment checklist (from P7_POST_AZURE_FINAL_PROOF_PACKET.md)
- [ ] Execute AzD/Bicep deployment pipeline
- [ ] Verify deployment succeeds

---

### Step 5 — Post-Deploy Validation (P7 Gates)

**Timeline:** 1–2 hours  
**Owner:** QA / Release Engineering  
**Prerequisites:** Deployment complete

- [ ] Run 6-gate validation:
  1. Health endpoint responds (HTTP 200)
  2. Database connectivity verified
  3. Authentication flow works
  4. Authorization boundaries enforced (cross-school access blocked)
  5. Performance meets baseline (< 200ms response time)
  6. Data isolation verified (School A cannot see School B)
- [ ] All 6 gates must PASS
- [ ] Rerun Judgment Day scorecard

---

### Step 6 — Final GO Packet Commit

**Timeline:** 30 minutes  
**Owner:** Release Engineering  
**Prerequisites:** Steps 4–5 complete

- [ ] Compile final GO packet with:
  - Founder/PO acceptance signature
  - Governance proof (admin-level controls)
  - Post-deploy validation results (6 gates)
  - Judgment Day scorecard (target 500+)
  - Decision approval metadata
- [ ] Commit with message: "release: FINAL GO approval and deployment evidence (May 5)"
- [ ] Tag: `v0.5.0-prod` or equivalent

---

## Decision Gate

**Current State:** GO-CANDIDATE  
**Unblock Condition:** Phase 1 items 1–3 complete  
**Next State:** Production GO → Deploy

---

## Risk Summary

| Risk | Level | Status | Mitigation |
|------|-------|--------|-----------|
| Founder/PO acceptance missing | 🔴 HIGH | Phase 1 Priority 1 | Get signature now |
| Governance API proof incomplete | 🟡 MEDIUM | Phase 1 Priority 2 | Re-run with admin token |
| Health-watch intermittent failures | 🟡 MEDIUM | Phase 1 Priority 3 | Monitor next 3 runs |
| Engineering gates | 🟢 LOW | ✅ LOCKED | All passing on main |

---

## Quick Reference: Who Does What

| Owner | What | When | Duration |
|-------|------|------|----------|
| Leadership | Sign final acceptance | Now | 1 hour |
| Release Eng | Admin proof re-run | After PO signs | 30 min |
| On-call ops | Monitor health-watch | Now (passive) | 1–3 hours |
| DevOps | Deploy | After Phase 1 done | 1–2 hours |
| QA / Eng | Post-deploy validation | After deploy | 1–2 hours |
| Eng | Final packet commit | After validation | 30 min |

---

## Commit This Checklist

This checklist becomes the operational task list for the next 4–6 hours.

```bash
git add PRODUCTION_GO_PRIORITIES_CHECKLIST.md
git commit -m "docs(release): priorities checklist for production GO execution

- Phase 1 (unlock): founder/PO signature, governance re-proof, health-watch confirm
- Phase 2 (deploy): deployment, post-deploy validation, final packet
- Ready for execution: all prerequisites documented, owners assigned"
```

---

**Authority:** Release Engineering  
**Reference:** PRODUCTION_READINESS_DECISION_20260505.md  
**Last Updated:** 2026-05-05T19:00 UTC
