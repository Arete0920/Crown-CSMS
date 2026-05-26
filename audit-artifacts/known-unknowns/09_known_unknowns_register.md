# Known Unknowns Register (Discovery Closure)

Generated from discovery-only evidence pass. No repair patches applied.

Status legend: PASS, FAIL, PARTIAL, MISSING, STILL_UNKNOWN.

| ID | Unknown Concern | Status | Classification Rationale | Evidence |
|---|---|---|---|---|
| KU-01 | Exact failed tests/proof-ceremony root cause is unclear | PASS | Exact assertion-level signatures are captured for sampled runs: billing summary returned 403 instead of 200, billing installment-plan RBAC write tests failed with 403 blocks, wizard session creation failed with 403 instead of 201, and prod integrity recorded deployed SHA mismatch. | 12_first_error_signatures.md; 11_first_blocker_extraction.md |
| KU-02 | Dashboard content may still be static/sandbox instead of live | FAIL | Many dashboard templates still import and display BASE_NOTE with explicit sandbox-preview wording; runtime template also defaults to base faith-community data. | 04_dashboard_live_data_inventory.md |
| KU-03 | Parent route protection may still allow direct unguarded renders | FAIL | Router shows direct ParentDashboard routes at /parent and /parent/dashboard without RoleGuard wrapping in those route entries. | 06_parent_journey_unknowns.md; frontend/dashboards/src/routes/router.jsx |
| KU-04 | Parent journey release gate might be unverified or unstable | PASS | Parent sandbox gate script, PASS output markers, and latest PASS artifact references are present in release hardening evidence. | 03_parent_sandbox_gate_inventory.txt |
| KU-05 | RBAC/tenant-isolation posture may not be fully proven in current state | PARTIAL | Authoritative KU-05 pass was started and captured repo/discovery/backend-check evidence, but targeted backend RBAC/tenant test section did not complete and frontend guard test output is missing in the artifact, so end-to-end proof remains incomplete on current SHA. | 14_ku05_authoritative_rbac_tenant_runtime_proof.md; 07_security_rbac_unknowns.md |
| KU-06 | CROWN core brand asset set may be incomplete | PASS | CROWN manifest assets resolve 7/7 present. | audit-artifacts/brand-integration/07_brand_asset_readiness_snapshot.json |
| KU-07 | CROWN favicon bundle may be missing | FAIL | Favicon readiness shows 0/6 present. | audit-artifacts/brand-integration/07_brand_asset_readiness_snapshot.json |
| KU-08 | Microsoft official logos may be missing/unregistered | FAIL | Microsoft manifest assets resolve 0/17 present; source register remains pending official source/reviewer entries. | audit-artifacts/brand-integration/07_brand_asset_readiness_snapshot.json; 08_microsoft_asset_unknowns.md |
| KU-09 | Local release state may be diverged from authoritative remote | FAIL | Branch is behind origin/main by 16 with a large dirty tree/untracked set, creating merge and truth-risk for release claims. | 02_local_vs_github_gap_inventory.txt |
| KU-10 | Production health endpoint/commit parity unknown | FAIL | Direct probe now captured: live health build_sha does not match referenced deploy run headSha, so parity is no longer unknown and is currently failing. | 13_production_parity_probe.md; 12_first_error_signatures.md |

## Closure Summary

- Closed with definitive PASS/FAIL/PARTIAL: KU-01 through KU-10.
- No contradiction found against prior parent sandbox PASS evidence.
- Highest-impact unresolved release blockers from this pass: KU-02, KU-03, KU-07, KU-08, KU-09, KU-10.
