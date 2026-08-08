# CROWN Architecture Review — 2026-08-08

**Status:** Current-main architecture inspection record  
**Reviewed source:** `5c52cc7cc8c1c2e4842fc88aea71eea7e20605d8`  
**Authority boundary:** This record reports architecture findings. It does not change the certified production identity or authorize deployment.

## Review objective

Inspect the live repository architecture before owner handoff and distinguish:

- verified architectural strengths;
- bounded defects that can be safely corrected before handoff;
- compatibility/convergence debt that must not be collapsed without migration and rollback evidence;
- stale architecture documentation that no longer describes current source accurately.

## Verified strengths

1. Canonical multi-tenant security contract exists through ADR-0001 and `request.crown_tenant`.
2. Protected tenant selection fails closed and supports explicit, audited override authority.
3. Canonical operational family/guardian/student write authority is defined through ADR-001.
4. A canonical frontend transport exists in `frontend/dashboards/src/utils/authClient.js` and owns API-base resolution, authentication, tenant propagation, timeout/cancellation, credentials, correlation, and structured failures.
5. Shared frontend wrappers (`api/client.js`, `api/request.js`, `api/apiClient.js`, `services/api.js`) converge on that canonical transport.
6. Existing transport contract tests prohibit reintroduction of known duplicate clients.
7. The active Celery communications outbox binds each delivery to an explicit school tenant context, restores context after execution, and applies bounded retry/dead-letter behavior.
8. Exact release identity, immutable tagging, tenant/RBAC certification, payment fail-closed behavior, and release authority are separately governed by the current release records.
9. Current dashboard architecture uses explicit registry/API-contract semantics rather than inferred route contracts, and role-scoped navigation fails closed rather than exposing broad fallback navigation.

## Verified bounded defects for immediate correction

### A-01 — stale client-supplied demo-role compatibility authority

`backend/crown_api/dashboards/views.py` still reads `X-Demo-Role` when deciding whether a Heritage sandbox user may receive sample dashboard payloads. `backend/crown_api/settings.py` still allows `x-demo-role` through CORS.

The current frontend dashboard client explicitly does not forward `X-Demo-Role`; authenticated sandbox sessions already create deterministic server-side `UserRole` records. Keeping the header as an authorization selector creates unnecessary duplicate authority.

**Required correction:** derive the permitted Heritage sandbox persona from authenticated server-side school/role state only; remove `x-demo-role` from active CORS allowance; add negative proof that a forged header cannot grant sample access.

### A-02 — canonical frontend transport not universal

The repository contains a canonical authenticated transport, but multiple frontend modules still call `globalThis.fetch` directly. Some are valid bootstrap/public/test exceptions; others are protected operational API consumers and duplicate authentication, tenant, timeout, error, or provenance behavior.

**Required correction:** inventory and classify direct-fetch sites; migrate protected operational calls to the canonical transport; retain only explicit bootstrap/public/external/test exceptions; add an enforcement contract so new protected direct-fetch sites fail CI.

### A-03 — mixed live/demo Board Executive loader

`frontend/dashboards/src/hooks/useBoardExecutiveData.js` manually constructs Authorization and tenant headers, calls four API endpoints directly, overlays successful responses onto demo defaults, and marks the aggregate live when any endpoint succeeds.

**Risk:** mixed provenance and transport-policy bypass.

**Required correction:** use the canonical transport and fail closed on incomplete live provenance for production-facing use, or explicitly classify the hook as demo-only and remove it from certified/live routes.

## Verified architecture documentation drift

- `SYSTEM_OVERVIEW.md` still says the frontend lacks a consolidated request transport, although the canonical transport and contract tests now exist.
- `SYSTEM_OVERVIEW.md`, `TENANT_ENFORCEMENT_IMPLEMENTATION_STATUS.md`, and `CANONICAL_IDENTITY_CONSUMER_INVENTORY.md` contain stale pre-certification release language or stale observed SHAs.
- These records must be reconciled to the certified-release/current-development identity boundary without claiming unverified convergence.

## Compatibility/convergence debt — do not destructively collapse before handoff

The following remain real architecture debt but require dependency/data/migration proof before removal:

1. three registered tenant middleware layers;
2. `core` versus `households`/`crown_api` identity compatibility domains;
3. `curriculum` versus `curricula` responsibility overlap;
4. finance/accounting/aid/billing/ledger/journal responsibility boundaries;
5. `integrations` versus `integrations_real` authority;
6. `academics` versus `academics_ro` boundary;
7. aggregate/projection domains (`student_records`, `student360`, `parent360`, `executive360`);
8. multiple legitimate authentication mechanisms requiring one normalized principal contract.

These are not safe two-day rename/delete targets. Any consolidation requires complete consumer inventory, data reconciliation where applicable, exact-head regression evidence, and rollback/forward-fix design.

## Required architecture decisions

The Decision Index currently has accepted authority for tenant resolution and canonical operational identity writes. Before material changes to the following boundaries, an ADR is required:

1. frontend transport and explicit exception policy;
2. domain ownership and allowed cross-domain dependencies;
3. asynchronous tenant/idempotency/retry/observability contract;
4. external integration adapter authority;
5. deployment/release/recovery topology;
6. reporting/analytics read models;
7. file/document storage and lifecycle authority;
8. payment adapter and activation contract.

Only decisions that describe current verified behavior should be accepted before handoff. Unimplemented future designs must remain proposed.

## Handoff target

Before owner turnover, CROWN should have:

- zero known high/critical architectural defect;
- one authoritative architecture gateway/map/decision index;
- no client-controlled duplicate security authority;
- one enforced protected frontend transport contract with explicit exceptions;
- current architecture status records;
- compatibility debt clearly isolated and non-destructive;
- successor-facing architecture decisions and migration boundaries that prevent accidental consolidation.
