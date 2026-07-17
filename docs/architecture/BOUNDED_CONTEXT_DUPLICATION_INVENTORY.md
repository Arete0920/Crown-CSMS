# CROWN Bounded-Context Duplication Inventory

Status: initial source inventory  
Authority: evidence lane under #1374  
Implementation authority: none; this document does not authorize deletion, migration, or consolidation by itself.

## Purpose

Identify overlapping application boundaries, model authorities, integration paths, middleware responsibilities, and financial domains that require explicit convergence decisions. The objective is to remove accidental duplication without collapsing legitimate bounded contexts.

## Classification

Each finding is classified as one of:

- **Canonical plus compatibility**: one authority exists and another path remains temporarily for migration or compatibility.
- **Potential duplicate authority**: two components appear to own the same responsibility and require dependency inventory.
- **Adjacent bounded contexts**: similar names represent distinct responsibilities and should remain separate if their contracts are explicit.
- **Historical or inactive**: retained for evidence or backward compatibility but not part of current runtime authority.

No component may be deleted solely because its name resembles another component.

## Current application-boundary findings

### 1. Curriculum: `curriculum` and `curricula`

Current settings register both applications.

Risk:

- duplicated course, subject, standards, scope-and-sequence, or curriculum-plan authority;
- divergent serializers and routes;
- unclear ownership for gradebook and classroom consumers.

Required evidence:

- model and migration inventory;
- URL and serializer inventory;
- imports and foreign keys from academics, classroom, gradebook, reporting, and wizards;
- data-row counts by tenant in representative environments;
- explicit decision: canonical, compatibility, or separate bounded contexts.

### 2. Financial domains: `apps.accounting`, `finance`, `aid`, `financial_aid`, `billing`, `ledger`, `journal`, and `finance_setup`

These applications may represent legitimate subdomains, but their authority boundaries are not obvious from registration alone.

Target responsibility model:

- **finance_setup**: policy and configuration input;
- **billing**: charges, invoices, payment schedules, receivables, and parent-facing balances;
- **financial_aid / aid**: applications, eligibility, awards, and award allocation;
- **ledger**: immutable accounting entries and balances derived from entries;
- **journal**: controlled journal workflows and approvals;
- **accounting / finance**: institutional accounting views, reporting, reconciliation, and configuration only where not owned above.

Risk:

- multiple sources of truth for balances, awards, transactions, or chart-of-account mappings;
- duplicate write paths;
- inconsistent tenant enforcement;
- reporting derived from non-canonical tables.

Required evidence:

- model-to-responsibility matrix;
- every write service and mutation endpoint;
- every balance or summary calculation;
- integrations with payment processors and CompuWerx;
- reconciliation path from parent charge through payment and ledger entry;
- explicit prohibition on float arithmetic, mutable ledger history, and single-entry authority.

### 3. Identity: `core` and `households`

Verified overlap exists for family or household, guardian, and student entities. Issue #1353 controls convergence.

Current direction:

- canonical operational writes use `core.Family`, `core.Guardian`, and `core.Student`;
- compatibility consumers remain and require complete dependency and data reconciliation before retirement.

Required evidence:

- foreign keys, serializers, endpoints, reports, seeds, portal access, and frontend contracts;
- identity mapping across admissions, enrollment, attendance, gradebook, billing, financial aid, and reporting;
- representative multi-tenant migration rehearsal;
- before-and-after counts and rollback proof.

### 4. Integrations: `integrations` and `integrations_real`

Current settings register both applications.

Risk:

- mock, scaffold, or compatibility integrations may coexist with production connector authority;
- route or service selection may depend on environment flags not centrally documented;
- duplicate provider clients may implement inconsistent retries, secrets, tenant binding, and audit behavior.

Required evidence:

- provider and client inventory;
- production, sandbox, mock, and disabled classifications;
- environment-selection rules;
- secret names and precedence;
- retry, timeout, idempotency, audit, and tenant contracts;
- explicit production authority for each provider.

### 5. Academics: `academics` and `academics_ro`

The `academics_ro` name suggests a read-only boundary, but that contract must be proven.

Required evidence:

- routes and permissions;
- database routers or read-only enforcement;
- write-path scan;
- relationship to reporting, dashboards, gradebook, and student records;
- decision whether `academics_ro` is a legitimate query boundary or duplicate API surface.

### 6. Student aggregate views: `student_records`, `student360`, `parent360`, and `executive360`

These may be presentation or projection contexts rather than duplicate systems of record.

Target rule:

- 360 applications may aggregate and project data;
- they must not silently become canonical write authorities for underlying student, guardian, billing, attendance, discipline, or academic records.

Required evidence:

- mutation endpoint scan;
- model ownership and denormalized projection inventory;
- refresh and consistency rules;
- tenant and role enforcement;
- source links for every displayed metric.

### 7. Platform tenancy: `core`, `tenants`, `platform_ops`, and three tenant middleware layers

Issue #1352 controls request-time tenant convergence.

Risk:

- tenant metadata and school identity may have overlapping ownership;
- request middleware currently divides isolation, header enforcement, and context stamping across multiple components;
- background jobs may not use the same canonical context contract.

Required evidence:

- canonical tenant and school entity decision;
- request attribute contract;
- exemption inventory;
- override permission and audit contract;
- task and scheduled-job tenant binding;
- middleware-equivalence tests before retirement.

### 8. Authentication: Django session, CROWN access token, SimpleJWT, Azure AD bearer, and custom JWT middleware

Multiple mechanisms can be legitimate because CROWN serves browser sessions, first-party tokens, and Microsoft identity integration. The concern is not mechanism count but inconsistent identity normalization.

Required evidence:

- authentication-mechanism matrix by route and client;
- canonical authenticated principal attributes;
- token precedence and failure behavior;
- tenant binding after authentication;
- role and permission normalization;
- removal of any mechanism with no active consumer only after usage proof.

## Cross-cutting architectural rules

1. Each persisted business fact must have one canonical write authority.
2. Compatibility paths must be named, measured, and time-bounded.
3. Projection and reporting contexts may duplicate data only with documented source, refresh, and reconciliation contracts.
4. Every tenant-scoped write and read must use the canonical tenant context.
5. Every external side effect must define timeout, retry, idempotency, audit, and failure semantics.
6. Every financial summary must trace to canonical immutable entries or explicitly authoritative source records.
7. Frontend surfaces must use one authenticated API transport contract.
8. Runtime startup must not own schema mutation.
9. No legacy path is removed before consumer inventory, data reconciliation, rollback, and same-SHA regression proof.

## Ordered follow-up lanes

1. #1387 — schema-deployment authority and web-start non-mutation.
2. #1352 — tenant request and background-context convergence.
3. #1353 — family, guardian, and student identity convergence.
4. Financial responsibility and write-authority matrix.
5. Curriculum and academics boundary decision.
6. Integration provider authority and environment-selection matrix.
7. Aggregate-view mutation prohibition and projection contracts.
8. Authentication principal-normalization matrix.
9. #1394 — CI proof hierarchy and duplicate execution reduction.
10. #1393 — clean-room transferability proof.

## Completion rule

This inventory is complete only when every registered application and shared platform service is assigned to an explicit bounded context with:

- owned entities;
- owned write operations;
- allowed dependencies;
- tenant contract;
- authentication and permission contract;
- API and event contracts;
- migration or compatibility status;
- tests and operational evidence.
