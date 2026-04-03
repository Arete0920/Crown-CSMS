# Final Investor Evidence Index

Generated: 2026-04-02  
Branch: `chore/github-cleanup-phase3-investor-evidence`

Purpose: single source of truth for evidence presence, status, and follow-up ownership.

Status legend:
- `PRESENT`
- `MISSING`
- `MANUAL_CAPTURE_REQUIRED`
- `PENDING_GREEN_RUN`

## 1. Security Gate Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/release/security-gate-evidence/codeql-blocking-evidence.png` | Screenshot of CodeQL blocking behavior on PR | `MISSING` | No screenshot committed yet | DevOps |
| `docs/release/security-gate-evidence/dep-audit-blocking-evidence.png` | Screenshot of dependency audit blocking PR | `MISSING` | No screenshot committed yet | DevOps |
| `docs/release/security-gate-evidence/secret-scan-blocking-evidence.png` | Screenshot of secret-scan blocking behavior | `MISSING` | Path reserved; proof not captured | DevOps |
| `.github/workflows/codeql.yml` | Source config for CodeQL workflow | `PRESENT` | Workflow exists and runs on main/develop + schedule | Engineering |
| `.github/workflows/dependency-audit.yml` | Source config for pip-audit and npm audit | `PRESENT` | Workflow exists; blocking behavior requires manual PR capture | Engineering |
| `.github/workflows/secret-scan.yml` | Source config for gitleaks scan | `PRESENT` | Workflow exists; blocking behavior requires manual PR capture | Engineering |
| `docs/release/SECURITY_GATES_EVIDENCE.md` | Security gate status and missing proof map | `PRESENT` | Canonical summary document | Engineering |

## 2. Branch Protection Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/release/branch-protection-export.json` | Branch protection/ruleset snapshot for main | `PRESENT` | Copied from `ruleset_main.json`; not a live API export | Engineering |
| `docs/release/security-gate-evidence/branch-protection-screenshot.png` | UI screenshot of branch protection settings | `MISSING` | Manual GitHub Settings capture required | Repo admin |
| `docs/release/BRANCH_PROTECTION_EVIDENCE.md` | Detailed interpretation and manual capture checklist | `PRESENT` | Includes expected/manual fields | Engineering |

## 3. Test/Proof Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `artifacts/golden-path-pytest-output.txt` | Golden path test run output | `MISSING` | Required final run artifact not committed | QA |
| `artifacts/tenant-isolation-pytest-output.txt` | Tenant isolation test output | `MISSING` | Required final run artifact not committed | QA |
| `docs/proof/GRADEBOOK_PROOF_2026-02-10.md` | Historical proof artifact | `PRESENT` | Documentary proof exists | Engineering |
| `docs/demo-proof/pp-003/proof/RUN1_PROOF.log` | Runtime proof log | `PRESENT` | Historical proof evidence | Engineering |
| `docs/demo-proof/pp-003/proof/RUN2_PROOF.log` | Runtime proof log | `PRESENT` | Historical proof evidence | Engineering |
| `AUDIT_PACK_20260330_193349/14_DEPLOY_PROD_RECENT.txt` | Recent prod deploy runs metadata | `PRESENT` | Latest sample shows failures only | DevOps |

## 4. OpenAPI Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/openapi/crown-openapi.yaml` | Exported OpenAPI schema | `PRESENT` | File exists in repo | Backend |
| `docs/openapi/README.md` | OpenAPI generation and verification instructions | `PRESENT` | Added in Phase 3 | Backend |
| `AUDIT_PACK_20260330_193349/06_BACKEND_URLS.txt` | URL export evidence | `PRESENT` | Report says show_urls unavailable in sampled env | DevOps |

## 5. Load/Performance Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `artifacts/load/crown-load-smoke.html` | Smoke load test report | `MISSING` | Not committed | QA |
| `artifacts/load/crown-load-FINAL.html` | Final load test HTML report | `MISSING` | Not committed | QA |
| `artifacts/load/crown-load-FINAL.csv` | Final load test CSV metrics | `MISSING` | Not committed | QA |
| `artifacts/load/` | Reserved canonical folder for load evidence | `PRESENT` | Folder created in Phase 3 | Engineering |

## 6. Documentation Package Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `README.md` | Product overview and release/governance map | `PRESENT` | Updated in Phase 3 |
| `SECURITY.md` | Security policy and controls | `PRESENT` | Updated links to evidence docs |
| `CHANGELOG.md` | Change history and release notes | `PRESENT` | Updated with Phase 3 entry |
| `docs/COMPLIANCE.md` | FERPA/COPPA operating framework | `PRESENT` | Existing |
| `docs/release/MODULE_INVENTORY.md` | Product scope inventory | `PRESENT` | Existing |
| `docs/release/WORKFLOW_CONSOLIDATION_PLAN.md` | CI/CD rationalization map | `PRESENT` | Existing + linked |
| `docs/release/FINAL_RELEASE_GATE.md` | Condition-by-condition release gate truth file | `PRESENT` | Added in Phase 3 |
| `docs/release/INVESTOR_REPO_REVIEW_GUIDE.md` | 5-minute reviewer walkthrough | `PRESENT` | Added in Phase 3 |
| `docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md` | Honest gap/defer registry | `PRESENT` | Added in Phase 3 |
| `docs/release/FINAL_SIGNOFF_CHECKLIST.md` | TC signoff checklist | `PRESENT` | Added in Phase 3 |

## 7. Repo Hygiene Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/repo-cleanup/CLEANUP_SUMMARY_PHASE1.md` | Root reorganization baseline | `PRESENT` | Existing Phase 1 output |
| `docs/repo-cleanup/CLEANUP_SUMMARY_PHASE2.md` | Workflow/governance cleanup summary | `PRESENT` | Existing Phase 2 output |
| `docs/repo-cleanup/PHASE3_FINAL_POLISH_SUMMARY.md` | Final investor-facing hygiene summary | `PRESENT` | Added in Phase 3 |
| `AUDIT_PACK_20260330_193349/01_TREE.txt` | Tree baseline evidence | `PRESENT` | Point-in-time tree |
| `AUDIT_PACK_20260330_193349/12_UNTRACKED_ARTIFACTS.txt` | Untracked artifact evidence | `PRESENT` | Point-in-time list |

## 8. Final Release-Gate Status

| Control | Status | Evidence |
|---|---|---|
| Final gate truth doc exists | `PRESENT` | `docs/release/FINAL_RELEASE_GATE.md` |
| Security/branch protection evidence docs exist | `PRESENT` | `docs/release/SECURITY_GATES_EVIDENCE.md`, `docs/release/BRANCH_PROTECTION_EVIDENCE.md` |
| Green-run evidence complete | `PENDING_GREEN_RUN` | Missing committed golden-path, tenant, and load reports |
| Branch protection UI capture complete | `MANUAL_CAPTURE_REQUIRED` | Missing screenshot from GitHub settings |

## 9. Deferred or Manual Items Still Required

| Item | Status | Next Action | Owner |
|---|---|---|---|
| Live branch protection API export for `main` | `MANUAL_CAPTURE_REQUIRED` | Export current settings from GitHub UI/API and replace snapshot file | Repo admin |
| Branch protection screenshot | `MANUAL_CAPTURE_REQUIRED` | Capture and commit `docs/release/security-gate-evidence/branch-protection-screenshot.png` | Repo admin |
| CodeQL blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Open PR with intentional violation and capture failed required check screenshot | Security lead |
| Dependency audit blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Open PR with vulnerable dependency and capture failed check screenshot | Security lead |
| Secret scan blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Capture failed secret scan check from PR | Security lead |
| Golden path test output | `PENDING_GREEN_RUN` | Run canonical golden path tests and commit output file in `artifacts/` | QA |
| Tenant isolation test output | `PENDING_GREEN_RUN` | Run tenant isolation tests and commit output file in `artifacts/` | QA |
| Final load reports | `PENDING_GREEN_RUN` | Run load test suite and commit smoke/final html+csv artifacts | QA |
| Health and integrity endpoint production capture with required fields | `MANUAL_CAPTURE_REQUIRED` | Capture valid `/api/health` and `/api/integrity` responses from prod with tenant header where needed | DevOps |
