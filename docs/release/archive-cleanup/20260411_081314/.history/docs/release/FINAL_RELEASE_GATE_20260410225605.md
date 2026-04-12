# Final Release Gate

Generated: 2026-04-02  
Scope: investor-facing final hygiene and evidence truth file  
Status scale: `PASS` | `PARTIAL` | `FAIL` | `MANUAL_VERIFICATION_REQUIRED`

## Condition-by-Condition Release Evaluation

| Condition | Status | Evidence / Rationale | Exact Next Step |
|---|---|---|---|
| All required cleanup steps complete and merged | `PARTIAL` | Phase 1 and Phase 2 artifacts exist (`docs/repo-cleanup/CLEANUP_SUMMARY_PHASE1.md`, `docs/repo-cleanup/CLEANUP_SUMMARY_PHASE2.md`); Phase 3 docs now assembled but not merged to main yet | Merge this branch and verify docs are visible on main |
| GitHub Actions green on main | `MANUAL_VERIFICATION_REQUIRED` | Latest sample deploy runs in `AUDIT_PACK_20260330_193349/14_DEPLOY_PROD_RECENT.txt` show failures; no current green-main export committed | Capture current main workflow run summary and attach in release evidence |
| Golden path green | `PASS` | Fresh proof captured in `artifacts/golden-path-pytest-output.txt`; the 2026-04-10 run passed `6 passed, 1 warning` | Keep the artifact current for the release SHA |
| Tenant isolation green | `PASS` | Fresh proof captured in `artifacts/tenant-isolation-pytest-output.txt`; the 2026-04-10 run passed `58 passed, 1 warning` after restoring fail-closed tenant-header behavior | Keep the artifact current for the release SHA |
| Load test PASS | `PASS` | Canonical artifacts now exist at `artifacts/load/crown-load-smoke.html`, `artifacts/load/crown-load-FINAL.html`, and `artifacts/load/crown-load-FINAL.csv` using the verified release-closeout load evidence | Re-run against prod only if a fresher release candidate needs updated numbers |
| Swagger/OpenAPI live and exported | `PARTIAL` | Export file exists at `docs/openapi/crown-openapi.yaml`; live route proof is documentary from source (`backend/crown_api/urls.py`) but no fresh runtime capture | Regenerate schema and capture successful `/api/docs/` and `/api/redoc/` runtime screenshots/log |
| Production health endpoint returns required fields | `PARTIAL` | `docs/release/security-gate-evidence/prod-health-capture.txt` now records a prod response with `env=prod`, `db=ok`, and `build_sha`; `prod-integrity-capture.txt` still shows `missing_tenant` until a school-scoped authenticated capture is taken | Capture a tenant-scoped `/api/integrity/` response from prod |
| Branch protection evidence captured | `PARTIAL` | `docs/release/branch-protection-export.json` has been refreshed from the live GitHub API, and the stale CodeQL required context has been corrected from `CodeQL / Analyze` to the live `CodeQL` check; the GitHub UI screenshot is still missing | Capture the GitHub settings screenshot and add it to `docs/release/security-gate-evidence/` |
| Governance docs live in repo | `PASS` | Present: `docs/release/BRANCH_PROTECTION_EVIDENCE.md`, `docs/release/SECURITY_GATES_EVIDENCE.md`, `docs/release/FINAL_SIGNOFF_CHECKLIST.md`, Phase 2 governance docs in `docs/repo-cleanup/` | Keep synchronized when controls change |
| GitHub metadata set (labels, branch rules, required checks visibility) | `MANUAL_VERIFICATION_REQUIRED` | PR triage exists (`docs/repo-cleanup/PR_TRIAGE_PHASE2.md`) but no committed metadata export proving labels/rulesets as configured today | Export labels/rules metadata and include snapshot |
| PR backlog reduced to acceptable state | `PARTIAL` | Current backlog and resolution path are documented in `docs/release/PR_ISSUES_CONCERNS_ACTION_PLAN.md`; open PR count remains above target and includes DIRTY/conflict PRs | Execute Priority 1 merge sequence and close/resolve DIRTY PRs (#611, #600) |
| Investor evidence bundle assembled | `PASS` | `docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md` created with explicit statuses and owners | Execute manual captures and green runs to promote partial controls to pass |

## Current Gate Decision

Overall release gate state: `PARTIAL`

Reason:
- Documentation and governance package is now assembled and externally reviewable.
- Critical runtime evidence (green runs, load reports, branch protection screenshots, live endpoint captures) remains pending manual capture.

## Non-PASS Items Requiring Closure Before Full Launch Readiness

1. Live branch-protection screenshot from GitHub settings
2. Security gate blocking screenshots (CodeQL, dependency audit, secret scan)
3. Tenant-scoped `/api/integrity/` production capture with the required fields
4. Fresh green-on-main run proof for the release SHA
5. OpenAPI/runtime cleanup needed for full green signoff
