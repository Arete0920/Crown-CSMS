# CROWN Tenant Convergence Current Inventory

Status: active inventory under #1352 and #1374  
Observed main SHA: `12f2af47abdebcf459f8d009d04538cc031348d7`  
Release posture: production not approved

## Verified current contract

- `request.crown_tenant` is the request-time authority.
- Direct `UserAccount.school` is the primary authenticated fallback.
- Exactly one role-derived school may be used as an unambiguous compatibility fallback.
- Multiple role-derived schools remain ambiguous and fail closed.
- Ordinary staff status does not authorize cross-school selection.
- Authorized support or superuser selection requires explicit authority and audit evidence.
- Assigned authenticated principals cannot cross schools through a conflicting header.
- The unassigned forced-auth adapter is limited to test-fixture compatibility.

## Completed source work

- ADR-0001 established compatibility-first convergence.
- Canonical tenant context and conflicting-header denial are merged.
- The authenticated `whoami` proof consumes canonical context.
- PR #1419 settled fallback, ambiguity, override, and forced-auth fixture behavior.
- PR #1420 corrected live-runtime artifact promotion and passed exact-head repository CI, including broad Tests and the sandbox evidence workflow.

## Remaining inventory

| Domain | Required evidence |
| --- | --- |
| Middleware and exemptions | complete before/after inventory and equivalence tests |
| Permissions and querysets | canonical-context migration and cross-school denial tests |
| Audit | actor, principal school, selected school, source, authorization basis, outcome, and correlation ID |
| Background work | explicit tenant envelope, retry isolation, and cleanup tests |
| Commands and integrations | explicit privileged scope and ambiguity rejection |
| Frontend | authenticated header propagation and browser/network proof |
| Tests | production binding separated from narrow fixture adapters |

## Runtime evidence still required

Against one unchanged deployed frontend/backend identity, capture screenshots, final URLs, authentication state, school context, console counts, failed network counts, observed API calls, provenance, and disposition for:

- `/school-admin-dashboard`, `/admin`, `/dash/admin`;
- `/teacher`, `/dash/teacher`;
- `/parent`, `/dash/parent`.

## Scope boundary

This inventory does not certify deployment, universal tenant convergence, middleware retirement, recovery, successor operation, or production authorization.