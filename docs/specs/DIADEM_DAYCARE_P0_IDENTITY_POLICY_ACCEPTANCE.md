# DIADEM-P0-01 — Standalone childcare policy proof

**Source baseline:** protected main `2805d5f9c78cbeb708021af91a3ca75e4b5f2dfb`.
**Branch:** `feature/diadem-daycare-p0-policy-20261030`.
**Status:** source-only, **not** an API, schema migration, deployed service, enrollment release, nor hosted acceptance.

## Non-overlap
Keep `backend/aftercare` as the canonical implementation spine in `DIADEM_DAYCARE_BUILD_CONTRACT.md`. Do not create `backend/daycare`. This slice adds only standalone data-independent policy logic and tests. It does not modify Extended Care PR #569, Camp, billing, tenant middleware, existing aftercare API behavior, or migration `0007`.

## Decisions and denial proofs
1. Child has canonical school/tenant, site, and household IDs; K–12 `Student` link is optional.
2. Guardian read needs authenticated, verified, child-specific active authority, matching household and tenant, clear custody state, and a valid timezone-aware authorization window. Household membership alone is insufficient.
3. Check-in eligibility needs matching tenant/site/child/program, active authorized staff, active READY care enrollment, correct date and weekday, explicit room capacity and staff-child ratio, known occupancy, and absence of duplicate check-in.
4. Missing policies or unknown states deny rather than default. Licensing ratios **must** be supplied from human-approved jurisdictional configuration, not inferred from K–12 settings.
5. Deterministic decisions are side-effect-free. They **cannot** prevent concurrent over-admission or substitute for database locks, complete emergency release controls, or actual authorization/authentication.

## Verification
Run from an environment with the actual repository and pytest:
```bash
PYTHONPATH=backend python -m pytest backend/aftercare/tests/test_daycare_policy.py -q
python -m compileall -q backend/aftercare/daycare_policy.py backend/aftercare/tests/test_daycare_policy.py
```
The source was also exercised in an isolated working directory: **73 pytest cases passed**, and Python compilation passed. This is **not** a repository-wide CI/DB/Azure assertion. The attached branch test file is equivalent but has been independently committed and awaits GitHub CI confirmation.

## Integration follow-up (OPEN)
- Align schema/migration ordering with Extended Care PR #569 before creating tenant-scoped persistent childcare child, verified per-child guardian authority, site, room, childcare enrollment, attendance and immutable audit models.
- Enforce active/trial standalone Daycare entitlement separately from AM, PM, and Camp; require proper RBAC and site scope for every API action.
- Under an atomic transaction with appropriate row locks, re-read enrollment, staffing and occupancy, re-evaluate policy, then commit check-in. Test concurrent arrivals and room transfers.
- Implement authorized release, compliance and operational acceptance, role-specific mobile dashboards, and school-only versus standalone operator access.
- Execute exact-SHA Django migrations, existing Aftercare regression, cross-tenant/permission tests, frontend and hosted synthetic acceptance before claiming completed Diadem delivery.
