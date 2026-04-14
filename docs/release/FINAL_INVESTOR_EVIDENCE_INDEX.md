# Final Investor Evidence Index

Generated: 2026-04-11
Branch: `fix/frontend-audit`

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
| `docs/release/security-gate-evidence/codeql-live-state.txt` | Live CodeQL default-setup and required-check evidence | `PRESENT` | Captures GitHub API proof that default setup is configured and `main` now requires `CodeQL` plus the contract/pytest/security gates | Engineering |
| `.github/workflows/dependency-audit.yml` | Source config for pip-audit and npm audit | `PRESENT` | Workflow exists; live branch protection now requires `dependency-review`, `Backend Python Dependency Audit`, and `Frontend Node Dependency Audit` | Engineering |
| `.github/workflows/secret-scan.yml` | Source config for gitleaks scan | `PRESENT` | Workflow exists; live branch protection now requires `secret-scan` | Engineering |
| `docs/release/SECURITY_GATES_EVIDENCE.md` | Security gate status and missing proof map | `PRESENT` | Canonical summary document | Engineering |

## 2. Branch Protection Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/release/branch-protection-export.json` | Branch protection/ruleset snapshot for main | `PRESENT` | Refreshed from the live 2026-04-11 GitHub API for `main`; shows the full 18-check required set including CodeQL and security gates | Engineering |
| `docs/release/security-gate-evidence/branch-protection-screenshot.png` | UI screenshot of branch protection settings | `MISSING` | Manual GitHub Settings capture required | Repo admin |
| `docs/release/BRANCH_PROTECTION_EVIDENCE.md` | Detailed interpretation and manual capture checklist | `PRESENT` | Includes expected/manual fields | Engineering |

## 3. Test/Proof Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `artifacts/golden-path-pytest-output.txt` | Golden path test run output | `PRESENT` | Fresh 2026-04-10 run captured from `backend/tests/test_golden_path.py` and `backend/tests/test_golden_path_bootstrap_school_create.py` | QA |
| `artifacts/tenant-isolation-pytest-output.txt` | Tenant isolation test output | `PRESENT` | Fresh 2026-04-10 run captured from the canonical tenant isolation suite | QA |
| `docs/proof/GRADEBOOK_PROOF_2026-02-10.md` | Historical proof artifact | `PRESENT` | Documentary proof exists | Engineering |
| `docs/demo-proof/pp-003/proof/RUN1_PROOF.log` | Runtime proof log | `PRESENT` | Historical proof evidence | Engineering |
| `docs/demo-proof/pp-003/proof/RUN2_PROOF.log` | Runtime proof log | `PRESENT` | Historical proof evidence | Engineering |
| `AUDIT_PACK_20260330_193349/14_DEPLOY_PROD_RECENT.txt` | Recent prod deploy runs metadata | `PRESENT` | Latest sample shows failures only | DevOps |

## 4. OpenAPI Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `docs/openapi/crown-openapi.yaml` | Exported OpenAPI schema | `PRESENT` | File exists in repo and schema export now completes again after the 2026-04-11 compatibility fix | Backend |
| `docs/openapi/README.md` | OpenAPI generation and verification instructions | `PRESENT` | Added in Phase 3 | Backend |
| `AUDIT_PACK_20260330_193349/06_BACKEND_URLS.txt` | URL export evidence | `PRESENT` | Report says show_urls unavailable in sampled env | DevOps |

## 5. Load/Performance Evidence

| File Path | Purpose | Status | Notes | Owner |
|---|---|---|---|---|
| `artifacts/load/crown-load-smoke.html` | Smoke load test report | `PRESENT` | Canonical artifact path populated from verified release closeout load evidence | QA |
| `artifacts/load/crown-load-FINAL.html` | Final load test HTML report | `PRESENT` | Canonical artifact path populated from verified release closeout load evidence | QA |
| `artifacts/load/crown-load-FINAL.csv` | Final load test CSV metrics | `PRESENT` | Canonical artifact path populated from verified release closeout load evidence | QA |
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
| `docs/release/CROWN_MASTER_BINDER.md` | Governance canon and sequencing authority | `PRESENT` | Added in Priority #5 packaging tranche |
| `docs/release/CROWN_PACKAGING_TIER_CANON.md` | Commercial tiering and claim language canon | `PRESENT` | Added in Priority #5 packaging tranche |
| `docs/release/CROWN_MARKET_DECISION_MATRIX.md` | Market positioning and scope decision matrix | `PRESENT` | Added in Priority #5 packaging tranche |
| `docs/release/PILOT_INVESTOR_READINESS_PROOF_PACK.md` | Pilot and investor proof-pack assembly guide | `PRESENT` | Added in Priority #5 packaging tranche |
| `docs/release/PRIORITY_6_SELECTIVE_EXPANSION_CANON.md` | Priority #6 selective expansion governance canon | `PRESENT` | Added in Priority #6 expansion tranche |
| `docs/release/STANDALONE_ADDONS_PRODUCT_TRACK.md` | Standalone-capable add-ons expansion tracker | `PRESENT` | Added in Priority #6 expansion tranche |
| `docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md` | Priority #7 operating-company governance canon | `PRESENT` | Added in Priority #7 operating tranche |
| `docs/release/OPERATING_COMPANY_SYSTEM_BLUEPRINT.md` | Priority #7 implementation/support/scale execution blueprint | `PRESENT` | Added in Priority #7 operating tranche |
| `docs/release/PRIORITY_8_PARTNERSHIP_MARKET_CAPTURE_CANON.md` | Priority #8 partnership-led market capture governance canon | `PRESENT` | Added in Priority #8 market tranche |
| `docs/release/PARTNERSHIP_CHANNEL_EXECUTION_PLAYBOOK.md` | Priority #8 channel execution operating playbook | `PRESENT` | Added in Priority #8 market tranche |
| `docs/release/PRIORITY_9_MOAT_PROTECTION_CANON.md` | Priority #9 moat-protection and value-compounding governance canon | `PRESENT` | Added in Priority #9 moat tranche |
| `docs/release/MOAT_COMPOUNDING_EXECUTION_PLAYBOOK.md` | Priority #9 moat-compounding execution playbook | `PRESENT` | Added in Priority #9 moat tranche |

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
| Green-run evidence complete | `PRESENT` | `artifacts/golden-path-pytest-output.txt`, `artifacts/tenant-isolation-pytest-output.txt`, and `artifacts/load/*` are now committed as canonical evidence |
| Branch protection UI capture complete | `MANUAL_CAPTURE_REQUIRED` | Missing screenshot from GitHub settings |

## 9. Deferred or Manual Items Still Required

| Item | Status | Next Action | Owner |
|---|---|---|---|
| Live branch protection API export for `main` | `PRESENT` | `docs/release/branch-protection-export.json` has been refreshed from the live GitHub API; only the optional UI screenshot remains | Repo admin |
| Branch protection screenshot | `MANUAL_CAPTURE_REQUIRED` | Capture and commit `docs/release/security-gate-evidence/branch-protection-screenshot.png` | Repo admin |
| CodeQL blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Open PR with intentional violation and capture failed required check screenshot | Security lead |
| Dependency audit blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Open PR with vulnerable dependency and capture failed check screenshot | Security lead |
| Secret scan blocking screenshot | `MANUAL_CAPTURE_REQUIRED` | Capture failed secret scan check from PR | Security lead |
| Golden path test output | `PRESENT` | Fresh 2026-04-10 output is committed at `artifacts/golden-path-pytest-output.txt` | QA |
| Tenant isolation test output | `PRESENT` | Fresh 2026-04-10 output is committed at `artifacts/tenant-isolation-pytest-output.txt` | QA |
| Final load reports | `PRESENT` | Canonical smoke/final HTML+CSV artifacts are present in `artifacts/load/` | QA |
| Health and integrity endpoint production capture with required fields | `PARTIAL` | `docs/release/security-gate-evidence/prod-health-capture.txt` and `prod-integrity-capture.txt` are now committed from the latest audit-pack probe; `/api/health` is good, while `/api/integrity` still shows `missing_tenant` without a scoped header | DevOps |

