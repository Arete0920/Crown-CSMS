# CROWN Legacy API Route Classification

Status: controlled inventory only  
Authority: Stage 1 application-surface census / issue #1587  
Base commit: `6a40ed83c01764e139af7ba91951e12f9b98124a`

## Purpose

This ledger classifies the 118 declarations in `backend/crown_api/api_urls.py` before any route retirement, alias correction, or prefix repair. It does not authorize removal or behavioral changes.

The module is included by `backend/crown_api/api_v1_urls.py`, which is mounted twice by the project URL configuration:

- canonical mount: `/api/v1/`
- compatibility mount: `/api/`

Most declarations are unprefixed and therefore resolve naturally under both mounts. Twenty-nine declarations contain their own leading `v1/` segment. Those declarations invert the intended mount behavior:

- canonical mount produces `/api/v1/v1/...`
- compatibility mount produces `/api/v1/...`

## Reconciled declaration counts

| Class | Count | Treatment |
|---|---:|---|
| Internally `v1/`-prefixed declarations | 29 | Hold for consumer and resolver review; do not remove blindly |
| Deprecated director compatibility routes | 8 | Preserve until consumer evidence supports retirement |
| Other direct routes | 68 | Retain; review mutations separately for authorization and tenant boundaries |
| Other nested includes | 13 | Retain; inspect precedence and child route ownership separately |
| **Total** | **118** | Exact reconciliation |

The 29 internally prefixed declarations consist of 28 direct routes and one nested include (`v1/finance-setup/`).

## Internally prefixed families

| Family | Count |
|---|---:|
| Finance metrics and revenue integrity | 5 |
| Finance setup include | 1 |
| Onboarding | 3 |
| Help | 1 |
| Solomon | 6 |
| Board intelligence | 7 |
| Support | 3 |
| Analytics and export | 2 |
| Public status | 1 |
| **Total** | **29** |

## Deprecated director routes

The following eight routes are explicitly documented in source as deprecated compatibility surfaces:

- `director/aid/summary/`
- `director/finance/summary/`
- `director/registrar/summary/`
- `director/dashboard/`
- `director/priority/`
- `director/actions/`
- `director/timeline/`
- `director/force_seed_user/`

Their deprecated label is not sufficient evidence for deletion. Consumer references, resolver winners, authentication, tenant boundaries, and replacement-path parity must be proven first.

## Verification contract

`backend/tests/test_legacy_api_url_classification.py` binds:

1. the exact 118-declaration total;
2. the 104 direct / 14 include split;
3. the exact 29 internally prefixed declarations;
4. the exact eight deprecated director routes;
5. the exact 13 non-`v1/` nested includes;
6. the dual `/api/v1/` and `/api/` mounts;
7. the resulting prefix inversion.

The test is intentionally read-only and does not modify routing.

## Required next evidence before route changes

1. Resolve concrete probes for every internally prefixed family under both mounts.
2. Search frontend, backend, tests, scripts, documentation, and external integration contracts for consumers.
3. Classify each route as canonical, compatibility-only, unreachable, shadowed, or unreferenced.
4. For mutation routes, verify authentication, permission, and tenant-scoping behavior.
5. Introduce aliases or deprecation evidence before deleting any active path.
6. Apply changes in small family-specific pull requests with exact resolver tests.

## Release authority

This inventory improves traceability only. It does not alter deployment or release authority. Production remains **NOT APPROVED**.
