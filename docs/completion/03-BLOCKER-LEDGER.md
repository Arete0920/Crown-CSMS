# Crown2026 — Blocker Ledger

## Blocker template

- Blocker ID:
- Title:
- Bucket:
- Severity:
- Current Status:
- Exact Evidence:
- File(s) involved:
- Owner:
- Exit Criteria:
- Proof Artifact:
- Notes:

---

## BLOCKER-001
- Blocker ID: BLOCKER-001
- Title: gradebook-proof failing
- Bucket: Branch blocker
- Severity: Critical
- Current Status: Open
- Exact Evidence: PR 577 check gradebook-proof is COMPLETED FAILURE
- File(s) involved: frontend/dashboards/tests/api/gradebook-api-proof.spec.ts, frontend/dashboards/tests/ui/gradebook-ui-proof.spec.ts
- Owner: PR 577 owner
- Exit Criteria: gradebook-proof check is COMPLETED SUCCESS on current head SHA
- Proof Artifact: https://github.com/tcmegahan/Crown2026/actions/runs/23117229036/job/67144801513
- Notes: Required merge check is currently red.

---

## BLOCKER-002
- Blocker ID: BLOCKER-002
- Title: Proof Smoke (Playwright) failing
- Bucket: Branch blocker
- Severity: Critical
- Current Status: Closed
- Exact Evidence: Proof Smoke (Playwright) is COMPLETED SUCCESS
- File(s) involved:
- Owner:
- Exit Criteria: Already met in current snapshot
- Proof Artifact: https://github.com/tcmegahan/Crown2026/actions/runs/23117229040/job/67144801498
- Notes: Local proof set also passed (11/11) in _local_playwright_after_fix.log.

---

## BLOCKER-003
- Blocker ID: BLOCKER-003
- Title: dashboard-ui-gates failing
- Bucket: Branch blocker
- Severity: Critical
- Current Status: Closed
- Exact Evidence: dashboard-ui-gates is COMPLETED SUCCESS
- File(s) involved:
- Owner:
- Exit Criteria: Already met in current snapshot
- Proof Artifact: https://github.com/tcmegahan/Crown2026/actions/runs/23117229017/job/67144801413
- Notes: Required merge check is green.

---

## BLOCKER-004
- Blocker ID: BLOCKER-004
- Title: CodeQL failing
- Bucket: Branch blocker / Production blocker
- Severity: High
- Current Status: Open
- Exact Evidence: CodeQL check is COMPLETED FAILURE on PR 577
- File(s) involved: .github/workflows/* (CodeQL workflow surface), repository source scanned by CodeQL
- Owner: PR 577 owner + security reviewer
- Exit Criteria: CodeQL overall check is COMPLETED SUCCESS
- Proof Artifact: https://github.com/tcmegahan/Crown2026/runs/67144861882
- Notes: Analyze jobs completed, but aggregate CodeQL check failed.

---

## BLOCKER-005
- Blocker ID: BLOCKER-005
- Title: Demo token acquisition contract unstable
- Bucket: Branch blocker / Investor blocker
- Severity: Critical
- Current Status: Closed
- Exact Evidence: Token request/parse/fail-fast behavior is explicitly defined in .github/workflows/proof-gradebook.yml (POST /api/dev/token/, X-Demo-Key, empty-response hard fail, access/access_token parsing)
- File(s) involved: .github/workflows/proof-gradebook.yml, docs/completion/05-PROOF-CONTRACT.md
- Owner: PR 577 owner
- Exit Criteria: Met in current snapshot
- Proof Artifact: .github/workflows/proof-gradebook.yml:151; .github/workflows/proof-gradebook.yml:153; .github/workflows/proof-gradebook.yml:171; .github/workflows/proof-gradebook.yml:172; .github/workflows/proof-gradebook.yml:196; .github/workflows/proof-gradebook.yml:199
- Notes: Contract is documented and evidence-backed; this does not imply gradebook-proof check itself is green.

---

## BLOCKER-006
- Blocker ID: BLOCKER-006
- Title: Proof route contract unstable
- Bucket: Branch blocker
- Severity: High
- Current Status: Closed
- Exact Evidence: Route contract table is now evidence-linked to router and proof tests with source line anchors
- File(s) involved: docs/completion/04-ROUTE-CONTRACT.md, frontend/dashboards/src/routes/router.jsx, frontend/dashboards/tests/proof-smoke.spec.ts
- Owner: PR 577 owner
- Exit Criteria: Met in current snapshot
- Proof Artifact: docs/completion/04-ROUTE-CONTRACT.md
- Notes: Route mapping now distinguishes proven behavior from UNPROVEN behavior.

---

## BLOCKER-007
- Blocker ID: BLOCKER-007
- Title: Proof heading contract unstable
- Bucket: Branch blocker
- Severity: High
- Current Status: Closed
- Exact Evidence: Proof contract headings/controls now reflect exact assertion granularity in smoke and UI suites (specific headings where asserted, generic h1/h2 where applicable)
- File(s) involved: docs/completion/05-PROOF-CONTRACT.md, frontend/dashboards/tests/proof-smoke.spec.ts, frontend/dashboards/tests/ui/student-dashboard-v2.spec.ts, frontend/dashboards/tests/ui/parent-dashboard-v1.spec.ts, frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts
- Owner: PR 577 owner
- Exit Criteria: Met in current snapshot
- Proof Artifact: docs/completion/05-PROOF-CONTRACT.md
- Notes: Local test run remains green in _local_playwright_after_fix.log.

---

## BLOCKER-008
- Blocker ID: BLOCKER-008
- Title: RC artifact SHA drift risk
- Bucket: Branch blocker / Production blocker
- Severity: High
- Current Status: Open
- Exact Evidence: frontend/dashboards/dist/release-candidate.json is missing (RC_MISSING)
- File(s) involved: frontend/dashboards/dist/release-candidate.json
- Owner: release owner
- Exit Criteria: RC artifact exists with build_sha/build_tag and matches certified SHA
- Proof Artifact: RC artifact check command output
- Notes: Cannot establish RC SHA truth while artifact is absent.

---

## BLOCKER-009
- Blocker ID: BLOCKER-009
- Title: Full 14-module acceptance unproven
- Bucket: Module blocker
- Severity: Critical
- Current Status: Open
- Exact Evidence: Module matrix not fully evidenced per module; many fields remain UNPROVEN
- File(s) involved:
- Owner:
- Exit Criteria: All 14 modules have evidence-backed status and exit criteria satisfied
- Proof Artifact: docs/completion/02-MODULE-ACCEPTANCE-MATRIX.md
- Notes: Presence of directories/pages is not sufficient for completion.

---

## BLOCKER-010
- Blocker ID: BLOCKER-010
- Title: Production deploy truth unproven
- Bucket: Production blocker
- Severity: Critical
- Current Status: Open
- Exact Evidence: No production frontend/backend deployed SHA verification in this snapshot
- File(s) involved:
- Owner:
- Exit Criteria: DEPLOYED VERIFIED evidence for frontend and backend
- Proof Artifact: UNPROVEN
- Notes: Local /api/health reports local-dev build identity only.

---

## BLOCKER-011
- Blocker ID: BLOCKER-011
- Title: Finance / ledger / integration proof unproven
- Bucket: Production blocker / Investor blocker
- Severity: Critical
- Current Status: Open
- Exact Evidence: Finance/ledger integration proof not attached as current release evidence packet
- File(s) involved:
- Owner:
- Exit Criteria: Evidence-backed proof of billing, payments, ledger, aid, and integration flows
- Proof Artifact: UNPROVEN
- Notes: Needs explicit run artifacts on current release SHA.

---

## BLOCKER-012
- Blocker ID: BLOCKER-012
- Title: Investor evidence packet missing
- Bucket: Investor blocker
- Severity: High
- Current Status: Open
- Exact Evidence: Investor checklist still missing evidence-backed completion values
- File(s) involved:
- Owner:
- Exit Criteria: Investor checklist fully populated with PASS/FAIL/UNPROVEN and linked evidence
- Proof Artifact: docs/completion/07-INVESTOR-READINESS-CHECKLIST.md
- Notes: This blocker remains until evidence packet is fully assembled.

---

## Additional blockers

### BLOCKER-013
- Blocker ID:
- Title:
- Bucket:
- Severity:
- Current Status:
- Exact Evidence:
- File(s) involved:
- Owner:
- Exit Criteria:
- Proof Artifact:
- Notes:

### BLOCKER-014
- Blocker ID:
- Title:
- Bucket:
- Severity:
- Current Status:
- Exact Evidence:
- File(s) involved:
- Owner:
- Exit Criteria:
- Proof Artifact:
- Notes:
