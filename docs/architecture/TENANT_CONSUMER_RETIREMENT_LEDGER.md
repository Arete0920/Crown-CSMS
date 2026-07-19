# CROWN Tenant Consumer Retirement Ledger

Status: active execution inventory under #1352  
Observed main SHA: `12f2af47abdebcf459f8d009d04538cc031348d7`  
Runtime authority: `request.crown_tenant`

## Settled rules

- Legacy school and tenant request fields are compatibility projections.
- Direct school assignment is the primary authenticated fallback.
- One role school is unambiguous; multiple role schools fail closed.
- Ordinary staff status does not grant cross-school authority.
- Support or superuser selection requires explicit authority and audit evidence.
- Assigned principals cannot cross schools through conflicting headers.
- The unassigned forced-auth path is limited to test-fixture compatibility.
- Background work must bind school context explicitly.

## Verified completed work

- ADR-0001 and canonical tenant context are merged.
- Conflicting ordinary-user headers are denied before business logic.
- `whoami` consumes canonical tenant context.
- PR #1419 settled fallback and fixture compatibility behavior.
- PR #1420 corrected live-runtime artifact promotion and passed broad Tests plus the sandbox evidence workflow.

## Retirement matrix

| Consumer | Retirement condition |
| --- | --- |
| Middleware | one enforcing path, one reviewed exemption list, cleanup tests green |
| Permissions | canonical context and complete denial matrix |
| Querysets | explicit school scoping and cross-school object tests |
| Views and serializers | no unclassified production alias reads |
| Audit | complete actor, source, authorization, outcome, and correlation fields |
| Background jobs | immutable tenant envelope with retry and cleanup proof |
| Commands and integrations | explicit privileged scope and ambiguity rejection |
| Frontend | deployed authenticated browser/network proof |
| Fixtures | production binding separated from narrow test adapters |

## Ordered execution

1. Inventory every alias read, write, and exemption.
2. Classify enforcement, compatibility, audit, task, script, integration, frontend, and test-only consumers.
3. Add structured tenant decision auditing.
4. Migrate permission and queryset consumers.
5. Prove request and background cleanup.
6. Consolidate exemptions.
7. Run same-SHA browser/network evidence.
8. Retire redundant middleware only after equivalence evidence.

## Scope boundary

Issue #1352 remains open until all production consumers are classified, background context is explicit, override decisions are auditable, redundant middleware is safely retired, and deployed evidence confirms behavior without broader access.