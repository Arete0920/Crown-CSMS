# P0 Repair Sequence (Post-Discovery)

Scope source: discovery-only artifacts 00-09. No code patched in this pass.

## 1) Confirmed Blockers

1. Dashboard still exposes sandbox/static data signals across role templates (KU-02, FAIL).
2. Parent dashboard routes include direct unguarded render paths (KU-03, FAIL).
3. Brand completeness gap: CROWN favicons are missing (KU-07, FAIL).
4. Brand compliance gap: Microsoft official assets are missing (KU-08, FAIL).
5. Release truth-risk: local branch behind remote by 16 with broad dirty/untracked state (KU-09, FAIL).
6. Production parity mismatch: live health build SHA does not match referenced deploy run SHA (KU-10, FAIL).

## 2) Known Unknowns Closed

1. Workflow instability/failure root-cause signatures confirmed at assertion level for sampled blocker runs (KU-01 now PASS in discovery scope).
2. Parent sandbox gate existence and latest PASS evidence confirmed (KU-04, PASS).
3. CROWN core manifest asset presence confirmed (KU-06, PASS).

## 3) Known Unknowns Still Open

1. Fresh authoritative RBAC/tenant-isolation runtime proof on current release head (KU-05 remaining portion).
- Current KU-05 artifact is PARTIAL: repo/discovery/backend check captured, but targeted backend RBAC/tenant + frontend guard proof output is incomplete in 14_ku05_authoritative_rbac_tenant_runtime_proof.md.

## 4) P0 Repair Order (When Repairs Are Authorized)

1. Freeze release truth baseline
- Create clean tracking branch from origin/main and isolate only release-critical deltas.
- Eliminate behind/dirty ambiguity before any behavioral repair claims.

2. Parent route hard-guard closure
- Wrap direct parent routes with role guard policy consistent with FAMILY_VIEW contract.
- Add route-level guard tests for /parent and /parent/dashboard to prevent regressions.

3. Dashboard live-data conversion pass
- Replace BASE_NOTE/sandbox preview feed path in priority role dashboards with real API-backed payloads.
- Fail gate if "Sandbox preview data shown" appears on any route marked ready.

4. Microsoft asset compliance closure
- Intake official Microsoft assets only, complete source register (source URL/date/reviewer), and verify manifest path existence 17/17.

5. CROWN favicon bundle closure
- Materialize required favicon files and verify readiness 6/6.

6. RBAC + tenant isolation authoritative proof rerun
- Execute current authoritative suites and retain immutable artifact outputs tied to commit SHA.

7. Workflow failure root-cause extraction
- Completed in discovery scope: first-error signatures captured in 12_first_error_signatures.md (403-vs-expected assertion failures and related failing test identifiers).

8. Production parity proof
- Completed in discovery scope: parity probe captured and classified FAIL in 13_production_parity_probe.md.

## 5) Do-Not-Touch List During P0

1. Do not perform broad visual redesign, refactor, or route rewiring beyond required blocker fixes.
2. Do not alter stable parent sandbox gate scripts/artifacts except for strictly required bug fixes.
3. Do not replace official-vendor policy with generated or inferred logos.
4. Do not mix unrelated tool-chain EOL/formatting churn into blocker PRs.
5. Do not claim GO/green unless artifacts prove each blocker closed at current commit.

## 6) Release Readiness Impact

- Current readiness is NOT GO due to multiple FAIL blockers (KU-02, KU-03, KU-07, KU-08, KU-09, KU-10).
- Earliest credible GO path requires: branch truth normalization, parent guard closure, live-data closure, brand completeness/compliance closure, and refreshed authoritative security/parity evidence.
