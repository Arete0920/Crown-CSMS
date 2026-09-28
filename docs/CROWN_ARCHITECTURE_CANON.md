# CROWN Architecture Canon

**Version:** 2.0  
**Status:** Current architecture authority  
**Authority:** Crown-CSMS platform doctrine  
**Repository:** `Arete0920/Crown-CSMS`

## 1. Purpose

This document defines the current architectural boundaries, ownership rules, integration constraints, and non-negotiable platform guardrails for Crown-CSMS. It must remain consistent with the Crown Master Binder product taxonomy and current executable repository behavior.

## 2. Layered architecture

Crown uses one strict product architecture:

1. **Core** — foundation and canonical truth.
2. **Modules** — bounded school operations built on Core truth.
3. **Add-ons** — optional differentiated products that integrate through governed contracts and do not own Core truth.

### 2.1 Core

Core owns shared platform behavior and canonical records required by the rest of Crown:

- authentication and session/request identity;
- persistent RBAC and permission vocabulary;
- tenant/school isolation;
- audit logging;
- shared API and backend contracts;
- shared frontend shell/design-system standards;
- canonical student, household/family, guardian and staff identity;
- canonical school, academic-year, term and enrollment authority;
- common integration and evidence boundaries.

**Rule:** Core owns truth. No module or add-on may create a competing system of record.

### 2.2 Modules

Modules implement major school operations using Core identities and governed services. Current product taxonomy includes first-wave modules such as Admissions, Re-enrollment, Billing/Tuition/Payments, Communications and Portals, with additional operational modules including Transportation, Food Service, Health/Nurse Office, Athletics/Activities and Board/administrative reporting.

Modules may own domain-specific transactional data, but references to students, families, staff, schools, academic periods and permissions must resolve through canonical Core authority or an explicitly documented compatibility adapter.

### 2.3 Add-ons

Add-ons provide optional differentiated capabilities such as Spiritual Life, Service/Outreach, PD Hub and Compass. An add-on may be independently packaged, but it must integrate through explicit APIs/services/events and scoped permissions. It may not bypass tenant isolation, mutate Core truth through hidden coupling, or create shadow identity records.

## 3. Canonical ownership rules

- One canonical owner exists for every production datum.
- Duplicate representations are permitted only as explicitly documented compatibility/read adapters during a governed convergence period.
- Compatibility structures are **not** alternate authorities.
- New production writes must target canonical authority unless a current ADR explicitly authorizes otherwise.
- Retirement of compatibility data requires COPY/COMPARE/CUTOVER/RETIRE proof where destructive migration could lose or mis-map data.
- Identity mapping must be deterministic and tenant-safe; name, email, list order or other heuristics may not silently merge records.

## 4. Security and tenant model

### 4.1 Persistent permission engine

- Server-side persistent permissions are authoritative.
- Caller-controlled role headers, frontend role claims and generic Django staff flags are not substitutes for Crown permissions.
- Every protected endpoint must enforce the correct domain/action permission and object scope.
- Navigation may reflect permissions, but UI hiding is never an authorization control.

### 4.2 Tenant isolation

- School/tenant scope is mandatory at the query and mutation boundary.
- Cross-school foreign-key and related-object assignments must be rejected or concealed as appropriate.
- Demo/sandbox behavior may not weaken tenant or authorization controls.
- Cross-tenant negative tests are required for security-sensitive domain paths.

### 4.3 Restricted data

Sensitive domains such as student records, pastoral/spiritual-life data, student care/discipline, health-related data and financial data require explicit least-privilege access beyond mere authentication.

## 5. Integration and API rules

- Cross-domain access occurs through governed service/API contracts or documented adapters.
- Modules must not import another domain's persistence model merely to shortcut an established contract when that creates competing ownership.
- API contracts must preserve tenant scope, authorization and stable identity semantics.
- External integrations remain fail-closed when credentials, contracts or tenant configuration are absent.
- Payment-provider implementation remains provider-agnostic until a provider is contractually selected and certified.

## 6. Frontend architecture

Crown maintains one shared frontend architecture:

- one application shell and role-aware navigation system;
- one design-token/component system;
- shared form, table, card, modal, feedback and wizard patterns;
- no production placeholder/fake data presented as live truth;
- dashboards consume governed domain APIs rather than becoming independent data authorities;
- accessibility and responsive behavior are platform concerns, not module-specific exceptions.

## 7. Compatibility and convergence

Some historical representations remain intentionally retained where destructive retirement has not yet been proven safe. Examples include documented Scheduling compatibility paths and student-identity boundaries. Their presence is controlled technical debt, not permission to expand duplicate models.

Every retained compatibility surface must have:

- an identified canonical target;
- bounded permitted consumers;
- no unexplained production writer;
- tenant-safe mapping rules;
- a retirement/convergence condition documented in an ADR, architecture record or current domain disposition.

## 8. Repository and release architecture

- `main` is the authoritative integrated source branch.
- One coherent reversible outcome per pull request is the default review unit.
- Required exact-head CI, security, schema, route, contract and repository-policy gates must pass before merge.
- Historical workflow runs, tags, branches, predecessor repositories and proof artifacts are provenance, not current runtime authority.
- Current repository certification does not by itself prove production deployment, rollback execution, restore execution or successor acceptance.

## 9. Prohibited architecture patterns

The following are prohibited unless a current approved ADR explicitly establishes a bounded migration path:

- shadow student/family/staff/school truth;
- caller-spoofable authorization;
- tenant-isolation shortcuts;
- duplicate production writers for the same canonical business entity;
- dashboard or wizard stores that become competing systems of record;
- ad hoc module-specific design systems;
- production placeholder/demo data masquerading as live data;
- undocumented compatibility models;
- stale predecessor documentation presented as current authority.

## 10. Amendment and verification

Architecture changes require:

1. current-main evidence and dependency review;
2. explicit ownership/boundary decision;
3. affected ADR/canon/documentation update;
4. security, tenant and contract regression coverage where applicable;
5. exact-head CI and review-thread closure;
6. expected-head protected merge.

Where the project operates under the approved solo-developer governance workaround, automated checks and complete evidence-backed review are compensating controls; they are not represented as independent human approval.

## 11. Authority precedence

If an older architecture, roadmap, predecessor or experimental document conflicts with this canon, the following precedence applies:

1. current executable `main` behavior and enforced security/data-integrity contracts;
2. current approved ADR/domain disposition;
3. this Architecture Canon;
4. current Crown Master Binder taxonomy;
5. historical planning/provenance material.

Conflicts must be reconciled rather than silently carried forward.
