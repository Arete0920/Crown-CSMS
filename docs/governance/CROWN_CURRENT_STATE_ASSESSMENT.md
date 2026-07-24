# CROWN Current-State Assessment

**Document ID:** CROWN-GOV-003  
**Status:** ACTIVE — Initial Controlled Baseline  
**Parent authority:** `docs/governance/CROWN_BUYER_READY_COMPLETION_CANON.md`  
**Repository evidence SHA:** `7fb6ca623e541d3f59a482e5bb13769b998403e8`  
**Assessment date:** 2026-07-24  
**Owner:** John Megahan  
**Controlling execution issue:** #1587

## Executive conclusion

CROWN is a broad, substantially implemented Christian-school management platform with extensive backend apps, frontend routes, dashboards, registered wizards, tenant and authentication controls, governance records, tests and evidence infrastructure. The repository is not a shallow prototype.

CROWN is not currently proven complete, production authorized, buyer ready, or transfer complete. The current governing decision remains **PRODUCTION NOT APPROVED**.

## Verified repository baseline

- `main` evidence SHA: `7fb6ca623e541d3f59a482e5bb13769b998403e8`.
- Buyer-ready completion canon is active and highest authority.
- Django uses custom user model `core.UserAccount`.
- Backend settings register more than 50 operational, platform and wizard applications.
- Backend routing exposes health, integrity, schema, version, authentication, tenant-aware API, dashboards, platform operations, subscriptions, integrations, Microsoft identity and persona routes.
- Wizard registry contains 28 active wizard entries and drives both installation and URL registration.
- Frontend contains a large route surface for role dashboards, school operations, parent/teacher/student workflows, dashboards, wizards and launch/sandbox surfaces.
- Dashboard registry includes 40 dashboard components across seven tiers, with role groups, readiness metadata and evidence hooks.
- Product control documents define seven control-layer areas plus 46 ordered module/platform areas and five required row-level matrices.

## Architecture posture

### Strengths

- Explicit Core / Modules / Add-ons architecture.
- Canonical tenant header and tenant context controls are enabled by default.
- Custom user model avoids dual authentication registration.
- Central wizard registry reduces additive configuration drift.
- Dashboard registry centralizes dashboard discovery and role metadata.
- Health, version, integrity and identity endpoints support deployment diagnostics.
- Audit, correlation and performance middleware are present.
- Production-dangerous flags fail closed when `DEBUG=False`.
- External payment processing is explicitly excluded and required to remain fail closed.

### Material weaknesses

- Three tenant-related middleware layers remain and require final convergence and evidence.
- Backend API aliases and frontend legacy aliases remain; canonical route ownership is not fully reconciled.
- Core and compatibility family/guardian/student models remain an unresolved authority boundary.
- Installed-app breadth is greater than the current evidence-backed functional inventory.
- Dashboard components and registry rows outpace proven module APIs and runtime evidence.
- Current module, data-ownership, permission and dashboard matrices are planning controls rather than completed evidence records.

## Functional posture

### Substantially implemented

- school and tenant context;
- user, identity, role and permission foundations;
- family, guardian, student and enrollment surfaces;
- academics, classroom, gradebook and student-record surfaces;
- admissions and re-enrollment workflows;
- billing, finance, accounting, ledger and financial-aid surfaces;
- communications and family/teacher/student portals;
- discipline, attendance, service hours, graduation and student care;
- HR, advancement, curriculum/PD, safety, transportation, facilities and athletics;
- spiritual life, portrait, outreach, board oversight and analytics;
- platform operations, subscriptions, entitlements, support and integrations;
- aftercare, summer camp, home academy and learning continuity;
- 28 registered configuration/operations wizards;
- 40 dashboard registry entries.

### Not yet proven comprehensively

- every module's authoritative model, service and API chain;
- every frontend route's canonical destination and negative-path behavior;
- every dashboard's live source, freshness, provenance, reconciliation and export rules;
- every wizard's full workflow, rollback, permissions and runtime behavior;
- all persona workflows in one deployed production-mode campaign;
- all cross-module side effects and reconciliation paths;
- all background tasks, scheduled jobs and integration retry/deduplication controls.

## Data posture

### Strengths

- Canon declares Core ownership and prohibits module duplication of institutional truth.
- Recent academics changes improve normal, queryset and bulk tenant-integrity enforcement.
- Financial and operational modules have documented ownership boundaries.
- Demo mode and synthetic data boundaries are explicitly governed.

### Blocking weaknesses

- Compatibility `households` models and `core` models remain parallel operational authorities in active consumers.
- Broad tenant relational integrity remains only partially proven across migrations, scripts, tasks, imports, admin and raw SQL.
- Data lineage, retention, legal hold, anonymization, deletion, offboarding and buyer extraction are not yet comprehensively evidenced.
- Import/export controls require format-by-format verification.

## Security and privacy posture

### Strengths

- Fail-closed production secret-key requirement.
- Production guards for permissive CORS and demo mode.
- Authentication, JWT, session and Microsoft identity surfaces.
- Tenant header requirement and tenant context middleware.
- Audit middleware, role guards, permission components and controlled policy matrices.
- Explicit restrictions on compliance and certification claims.

### Blocking weaknesses

- Complete action-level backend permission mapping is not reconciled with frontend role groups.
- Direct-route, export, redaction and small-cell tests are incomplete across sensitive modules.
- External secret-store rotation, revocation and break-glass exercises remain open.
- Student-data privacy, contractual, state-law and legal validation remains open.
- File-upload security and data-loss-prevention controls require complete inventory and evidence.

## Release and operational posture

- Current target is full production release authorization.
- Current decision is **PRODUCTION NOT APPROVED**.
- No approved final release tuple exists.
- Complete surface-to-proof mapping remains incomplete.
- Authenticated deployed crawler/Playwright evidence remains incomplete.
- Application rollback and database restore drills remain incomplete.
- External secrets operational exercises remain incomplete.
- CI proof hierarchy and duplicate-workflow rationalization remain incomplete.
- Final release notes and authority reconciliation remain incomplete.

## Buyer and transfer posture

### Established

- Sole ownership and final authority are clearly stated.
- Contributor attribution must be evidence-based.
- AI assistance cannot be represented as independent human authorship or approval.
- Buyer-ready and transfer-complete standards are explicitly defined.

### Not yet complete

- detailed IP chain-of-title package;
- contributor and contractor evidence ledger;
- open-source and commercial license inventory;
- verified commercial and financial claims register;
- external account, vendor, subscription, domain and credential inventory;
- clean-room operations rehearsal;
- buyer diligence and transfer package indexes;
- qualified legal, security, accessibility, accounting and technical reviews where required.

## Overall assessment

CROWN has strong implementation breadth and improving integrity controls, but breadth is ahead of reconciled proof. The correct program is not to add more feature scope. It is to finish traceability, consolidate authority, prove runtime and operations, close canonical-data and tenant gaps, and assemble the diligence and transfer controls required by the buyer-ready canon.