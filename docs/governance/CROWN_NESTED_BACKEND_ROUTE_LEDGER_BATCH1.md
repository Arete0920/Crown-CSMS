# CROWN Nested Backend Route Ledger — Batch 1

**Document ID:** CROWN-GOV-008  
**Status:** ACTIVE — Stage 1 Census in Progress  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Repository evidence SHA:** `fc4d6907a079efb3f8aedbd041c11d8f01a218f4`  
**Verification date:** 2026-07-24  
**Controlling issue:** #1587

## Purpose

Expand the highest-risk nested Django URL configurations into source-backed route groups and identify canonical-path, compatibility, permission, tenant, payment-exclusion and shadowing issues before runtime certification.

This ledger records URL declarations and directly inspected view controls. A route declaration does not prove runtime reachability, correctness or authorization. Router-generated leaves remain subject to executable resolver extraction because custom actions can add paths beyond standard list/detail routes.

## Batch scope and exact declaration counts

| URL configuration | Mounting path | Source declarations | Verified access posture | Primary open work |
|---|---|---:|---|---|
| `academics.urls` | dual-mounted through `api_v1_urls` at `/api/v1/` and `/api/` | 13 router registrations + 18 explicit paths; at least one confirmed custom router action | mixed read-only and writable; authentication and tenant/role logic present in inspected views | expand every router action and resolve duplicate roster paths |
| `households.urls` | dual-mounted through `api_v1_urls` | 3 read-only router registrations | authenticated; school scoped; guardian/student row scoping present | reconcile compatibility models with Core authority |
| `crown_api.billing_api.urls` | dual-mounted through `api_v1_urls` | 5 explicit paths | authenticated; tenant scoped; one endpoint adds finance-role control | reconcile action-level finance permissions |
| `payments.api_urls` | `/api/v1/payments/` only | 24 explicit paths | all inspected routes authenticated; provider actions held; finance/household controls vary by action | certify excluded-provider hold and permission map |
| `financial_aid.urls` | dual-mounted through `api_v1_urls` | 6 explicit paths | mixed: some financial-aid permission checks, some authentication-only | close action-level authorization inconsistency |
| `subscriptions.api.urls` | `/api/v1/subscriptions/` only | 4 explicit paths | authenticated tenant reads; cross-school GET/POST restricted to admin | negative cross-school and entitlement tests |
| `subscriptions.urls` | `/api/v1/admin/modules/` only | 4 explicit paths | Django admin plus canonical tenant context | direct-route and audit verification |
| `integrations.urls` | `/api/integrations/` only | 1 explicit path | authenticated staff/admin plus tenant scope | export privacy, completeness and audit proof |
| `integrations_real.urls` | dual-mounted at `connectors/` through `api_v1_urls` | 2 explicit paths | authenticated reads | enabled/disabled connector truth and secret ownership |
| `platform_ops.urls` | `/api/platform/` only | 3 explicit paths | `IsAdminUser`; cross-tenant by design; no tenant header required | privileged override, audit and provisioning rollback proof |
| `core.auth.urls` | `/api/iam/` only | 2 explicit paths | AAD bearer authentication plus `IsAuthenticated` | identity-to-tenant/role reconciliation |
| `crown_api.api_urls` | dual-mounted through `api_v1_urls` at both `/api/v1/` and `/api/` | 118 top-level declarations: 104 direct paths + 14 nested includes | mixed legacy, current, read, write, metrics and admin surfaces | canonical catalog, collision map, permission map and retirement decisions |

## Academics route findings

### Registered router resources

The URLConf registers 13 viewsets:

1. academic years;
2. terms;
3. courses;
4. sections;
5. grade levels;
6. curriculum sources;
7. units;
8. lessons;
9. publisher objectives;
10. submissions;
11. grades;
12. mastery records;
13. transcript entries.

The URLConf also declares 18 explicit paths for school profile, transcript aliases, student/parent section access, assessments, attendance, roster, assignment categories, assignments, lesson plans and lesson resources.

### Confirmed collision

`SectionViewSet` declares a router action at:

`academics/sections/{pk}/roster/`

The same URLConf later declares:

`academics/sections/<uuid:section_id>/roster/`

Because `include(router.urls)` is the first pattern in `academics.urls`, the router action is evaluated before the later explicit route for matching values. The legacy catch-all also declares `academics/sections/<str:section_id>/roster/` after the real academics include. These are one route family with multiple callbacks, not three independent certified endpoints.

**Disposition:** `ACTIVE` with route-authority reconciliation required.  
**Affected risks:** CROWN-RISK-002, CROWN-RISK-005, CROWN-RISK-019.  
**Primary proof:** `API_CONTRACT`; secondary `BACKEND_TEST` and `PLAYWRIGHT`.

## Households and Core-authority overlap

`households.urls` exposes read-only router resources for:

- households;
- guardians;
- students.

All three require authentication and school scoping. Household parent-role filtering and student domain scoping are present in the inspected viewsets.

The legacy catch-all later declares direct household and student paths that overlap the earlier router resources. The earlier includes win Django first-match resolution for equivalent paths.

Configuration safety does not resolve the broader duplicate-truth issue: active consumers still use compatibility `households` models while the canon requires Core ownership of institutional truth.

**Disposition:** `ACTIVE compatibility layer`.  
**Affected risks:** CROWN-RISK-003, CROWN-RISK-004, CROWN-RISK-019.  
**Primary proof:** `BACKEND_TEST`; secondary `API_CONTRACT`.

## Billing route inventory and permission finding

The billing API declares:

| Relative route | Method | Inspected control |
|---|---|---|
| `billing/households/<household_id>/open-invoices/` | GET | `IsAuthenticated`, tenant-scoped household existence check |
| `billing/payments/` | POST | `IsAuthenticated`, tenant context; creates ledger payment and allocations |
| `billing/payments/record/` | POST | `IsAuthenticated` + finance role; tenant scoped; audited |
| `billing/payments/<payment_id>/apply/` | POST | `IsAuthenticated`, tenant context; creates or updates allocations |
| `billing/runs/api/` | POST | JWT + `IsAuthenticated`, tenant context; creates billing run, charge and invoice |

The two general ledger-payment mutation paths and the billing-run creation path do not use the finance-role permission applied to `PaymentsRecordView`.

This is an action-level authorization inconsistency. It is not classified as a proven exploit without direct negative tests, but it cannot be marked reconciled.

**Disposition:** `ACTIVE`; permission reconciliation required.  
**Affected risk:** CROWN-RISK-005.  
**Primary proof:** `BACKEND_TEST` with direct-route negative cases.

## External-payment exclusion boundary

`payments.api_urls` declares 24 paths. The inspected source divides them into provider-dependent actions that fail closed and provider-neutral operations that remain active.

### Provider-dependent routes verified fail closed

| Route family | Method | Hold behavior |
|---|---|---|
| `intents/` | POST | authenticated; HTTP 503 provider-deferred response |
| `intents/<intent_id>/status/` | GET | authenticated; HTTP 503 and failed status |
| `accounts/<household_id>/methods/setup/` | POST | authenticated, tenant and household access checked; HTTP 503 |
| `accounts/<household_id>/methods/<method_id>/` | DELETE | authenticated, tenant and household access checked; HTTP 503 after local existence check |
| `disputes/<dispute_id>/actions/` | POST | authenticated, tenant and finance role checked; HTTP 503 |
| `exceptions/<exception_id>/retry/` | POST | authenticated, tenant and finance role checked; payment hold response before provider event load |

These six routes are classified `EXCLUDED_PAYMENT_PROCESSING` / `DISABLED_FAIL_CLOSED` pending runtime proof.

### Provider-neutral payment operations remain active

The remaining route families provide local ledger/account summaries, payment history, CSV statements, HTML receipts, saved-method metadata reads/default selection, provider-record reads, payout and exception administration, bank-statement import, and bank/payout reconciliation.

They do not initiate external checkout in the inspected source. They remain subject to authentication, tenant, finance-role, household-access, sensitive-export and audit verification.

Notable distinctions:

- saved-method setup and detach are held;
- selecting an existing local saved-method row as default remains an active local metadata mutation;
- exception retry is held, while exception ignore remains an active local workflow mutation;
- payout and dispute records are readable by finance roles, while provider dispute actions are held;
- bank-statement upload and payout matching are active provider-neutral accounting/reconciliation operations.

**Affected risks:** CROWN-RISK-005, CROWN-RISK-012, CROWN-RISK-020.  
**Primary proof:** `BACKEND_TEST`; secondary `API_CONTRACT` and `OPERATIONAL_DRILL`.

## Financial-aid permission inconsistency

The six financial-aid routes are:

- summary;
- drilldown;
- metrics;
- applications;
- awards;
- billing-run disbursement.

Summary and drilldown require authentication, tenant context and `financial_aid.view`; drilldown separately restricts rationale exposure. Metrics requires `financial_aid.view`.

Applications, awards and billing-run disbursement require authentication and tenant context in the inspected source but do not call the financial-aid permission helpers used by the other routes. Disbursement mutates billing/ledger state through the financial-aid service.

**Disposition:** `ACTIVE`; permission reconciliation required.  
**Affected risk:** CROWN-RISK-005.  
**Primary proof:** `BACKEND_TEST` with unauthorized-role and cross-tenant cases.

## Subscriptions and module administration

### Subscription API

- current-tenant entitlements: authenticated plus canonical tenant;
- plans and features: authenticated reads;
- school subscription operations: `IsAdminUser`, GET and POST, cross-school by explicit school ID.

### Module administration

- list modules: admin plus canonical tenant;
- activate module: admin plus canonical tenant;
- deactivate module: admin plus canonical tenant;
- start trial: admin plus canonical tenant.

These are high-impact entitlement mutations and require direct-route, audit, idempotency and cross-school negative testing.

**Disposition:** `ACTIVE privileged`.  
**Affected risks:** CROWN-RISK-004, CROWN-RISK-005.  
**Primary proof:** `BACKEND_TEST`.

## Integration and export routes

### OneRoster

`GET /api/integrations/oneroster/export/` requires authentication, staff/admin status and school scope. It exports organization, academic-session, course, class and enrollment CSV content in a multipart response.

The source comment mentions `users.csv`, while the inspected file builder emits five files and does not build a users file. This is a documentation-to-implementation mismatch requiring correction or implementation.

**Disposition:** `ACTIVE sensitive export`.  
**Affected risks:** CROWN-RISK-012, CROWN-RISK-020.  
**Primary proof:** `BACKEND_TEST`; secondary `MANUAL_REVIEW`.

### Connector health/status

`/api/v1/connectors/health/`, `/api/connectors/health/`, `/api/v1/connectors/status/` and `/api/connectors/status/` resolve through authenticated GET views when the dual-mounted URLConf is active.

They report service-layer health/status; they do not establish which connectors are enabled, correctly credentialed, contractually owned or operationally reconciled.

**Disposition:** `ACTIVE`.  
**Affected risk:** CROWN-RISK-020.  
**Primary proof:** `API_CONTRACT` plus `OPERATIONAL_DRILL`.

## Platform and identity routes

### Platform operations

The three platform routes require `IsAdminUser` and are intentionally cross-tenant without a tenant header:

- create school and queue provisioning;
- list schools;
- read provisioning status.

The create-school payload accepts a `payment_provider` value whose documented options include `stripe`, `manual` and `none`. Accepting configuration metadata does not itself execute an external payment, but this field must be constrained so excluded providers cannot become active through provisioning.

**Disposition:** `ACTIVE privileged`.  
**Affected risks:** CROWN-RISK-004, CROWN-RISK-005, CROWN-RISK-020.  
**Primary proof:** `BACKEND_TEST`; secondary `OPERATIONAL_DRILL`.

### Microsoft identity

Both `/api/iam/me/` and `/api/iam/health-auth/` require `AADBearerAuthentication` and `IsAuthenticated`.

They prove bearer-token validation and identity resolution only. Tenant membership, CROWN role mapping, entitlement mapping and parity with session/JWT identities remain separate requirements.

**Disposition:** `ACTIVE where configured`.  
**Affected risks:** CROWN-RISK-004, CROWN-RISK-005, CROWN-RISK-020.  
**Primary proof:** `API_CONTRACT`; secondary `PLAYWRIGHT`.

## Legacy catch-all findings

`crown_api.api_urls` contains 118 top-level declarations:

- 104 direct paths;
- 14 nested includes.

It is included under both `/api/v1/` and `/api/`. Its surface includes dashboard metrics, household/student reads, applications, ledger writes, billing, academics, onboarding, Solomon, board, support, analytics and multiple module includes.

Twenty-nine declarations inside the legacy URLConf begin with `v1/`. Under the canonical root mount they therefore resolve as `/api/v1/v1/...`; under the compatibility mount they resolve as `/api/v1/...`.

This produces an inverted compatibility condition: for those 29 declarations, the `/api/` compatibility mount creates the cleaner `/api/v1/...` path, while the canonical `/api/v1/` mount creates a doubled prefix.

The URLConf also retains deprecated director routes and multiple direct paths shadowed by earlier real module includes. Route presence must therefore be classified by resolver precedence, not by text search alone.

**Disposition:** `ACTIVE compatibility layer`; bounded retirement or formal retention required.  
**Affected risks:** CROWN-RISK-002, CROWN-RISK-005, CROWN-RISK-019.  
**Primary proof:** `API_CONTRACT` using executable Django resolver extraction.

## Errors and inconsistencies identified in this batch

1. Academics contains a router-generated roster path and a later explicit path for the same route family; the legacy catch-all adds a third declaration.
2. Billing payment creation/application and billing-run creation use broader authentication controls than the finance-role-protected payment-record endpoint.
3. Financial-aid application, award and disbursement routes do not use the financial-aid permission checks used by summary, drilldown and metrics.
4. The OneRoster module documentation lists `users.csv`, but the inspected builder emits five files and no users file.
5. The legacy catch-all contains 29 `v1/`-prefixed declarations inside a URLConf already dual-mounted at `/api/v1/` and `/api/`.
6. Platform provisioning accepts a payment-provider configuration value even though external payment processing remains excluded; activation must remain independently fail closed.

## Required next execution

1. Generate an executable Django resolver manifest at a settled source SHA, including callback, route name and precedence.
2. Expand all router custom actions, beginning with academics and households.
3. Add direct negative tests for the billing and financial-aid permission inconsistencies.
4. Verify all six provider-dependent payment routes return the authorized hold response in production-mode settings.
5. Reconcile or retire shadowed academics, households and legacy catch-all paths.
6. Correct the OneRoster file-contract mismatch or add the missing users export under an approved privacy model.
7. Map the 118 legacy declarations to `retain`, `redirect`, `supersede` or `remove` decisions.

## Current conclusion

Batch 1 materially advances Stage 1 but does not complete the backend route census. The highest-risk route groups are now source-inventoried, and six concrete inconsistencies are controlled. No route, permission, tenant, payment or integration surface in this ledger is certified solely by documentation.