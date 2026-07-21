# CROWN Identity Model Convergence Ledger

Status: canonical operational write authority accepted; compatibility convergence remains open under #1353  
Migration strategy: expand-contract; no destructive rename or table collapse  
Accepted authority: `core.Family`, `core.Guardian`, and `core.Student`

## Purpose

Define the evidence required to reconcile CROWN's three verified household, guardian/person, and student model sets without silent data loss, cross-tenant merging, broken portal access, or downstream financial and academic corruption.

This ledger implements the accepted write-authority decision. It does not prove row-level equivalence, authorize compatibility-table retirement, or approve production release.

## Verified model sets

### 1. `core.models` — canonical operational write spine

Relational operational identity records with real `School` foreign keys and downstream dependencies including user accounts, enrollment, tuition, ledger, attendance, gradebook, reporting, and portal behavior.

All new operational identity writes must target this family unless a separately reviewed compatibility exception is documented.

### 2. `households.models` — compatibility domain

Lightweight household, guardian, and student tables using bare `school_id` UUID fields and simplified attributes.

This family remains available for existing compatibility reads and contracts. It is not an approved canonical writer and may not be renamed, merged, or deleted before tenant-by-tenant reconciliation and rollback proof.

### 3. `crown_api.models_households` — person and membership compatibility domain

Person-centered structure with `Household`, `HouseholdMember` role relationships, and a `Student` person profile. Tenant ownership is not explicit at the household level and must be resolved before any retirement or consolidation decision.

This family remains an admissions-linked compatibility domain. It is not interchangeable with the canonical core family.

## Required dependency ledger

For every model set, record:

- application, model, database table, primary key type, and migration ownership;
- school or tenant ownership field and enforcement path;
- unique constraints and external identifiers;
- guardian/person-to-student relationship semantics;
- custody, pickup, emergency-contact, financial-responsibility, and portal roles;
- serializers, forms, endpoints, permissions, reports, signals, tasks, imports, exports, seeds, tests, and frontend contracts;
- foreign keys from admissions, enrollment, attendance, gradebook, billing, financial aid, ledger, discipline, student records, communications, and portals;
- current row counts by tenant and lifecycle status;
- unmatched, duplicate, orphan, null, and cross-tenant anomaly counts.

## Accepted authority and remaining decision criteria

The accepted operational write authority is `core.Family`, `core.Guardian`, and `core.Student` because this family currently provides:

1. explicit tenant ownership through `School` foreign keys;
2. the active relational dependency anchor for enrollment, tuition, ledger, user accounts, and other operational domains;
3. established uniqueness and portal-link semantics;
4. the merged, tenant-bound guardian-household wizard writer;
5. fail-closed cross-school validation and transactional write behavior.

The accepted write authority does not establish that either compatibility family is empty, semantically equivalent, safely removable, or fully reconciled. Retirement requires:

1. stable external and portal identity mapping;
2. deterministic mapping from both compatibility families;
3. compatibility strategy for active APIs, reports, imports, exports, and background work;
4. zero-unexplained reconciliation results by tenant;
5. rollback or forward-fix without losing canonical writes accepted during migration.

## Expand-contract sequence

1. Freeze the dependency and row-count baseline.
2. Define canonical identity keys and tenant invariants from the accepted ADR.
3. Add mapping tables or deterministic mapping functions without deleting legacy data.
4. Rehearse migration on a production-shaped non-production copy.
5. Backfill tenant by tenant with reconciliation totals.
6. Add compatibility reads or adapters where required.
7. Move any remaining writers by bounded domain only after inventory and equivalence proof.
8. Prove read equivalence and permission equivalence.
9. Observe production-shaped behavior for a defined period.
10. Retire legacy writers, then readers, then tables only after explicit disposition of every unmatched record and Product Owner approval.

## Cross-domain proof matrix

- admissions applicant-to-student conversion;
- enrollment and grade-level assignment;
- guardian portal authentication and authorization;
- custody and pickup restrictions;
- attendance and excuse workflows;
- gradebook and academic reporting;
- tuition, billing, payment allocation, and family ledger linkage;
- financial-aid household and student linkage;
- discipline, communications, and emergency contacts;
- imports, exports, reports, and 360 projections;
- tenant isolation for reads, writes, joins, reports, and background tasks.

## Reconciliation evidence

Each rehearsal and migration must produce, by tenant and entity:

- pre-count and post-count;
- mapped count;
- unmatched count;
- duplicate candidate count;
- orphan count;
- rejected cross-tenant relationship count;
- null or invalid identity count;
- manual-disposition count;
- referential-integrity result;
- rollback or forward-fix result.

## Prohibited shortcuts

- no model deletion because names appear equivalent;
- no cross-tenant matching by email, name, address, or phone alone;
- no silent ID regeneration that breaks external or portal references;
- no dual-write without idempotency, monitoring, and reconciliation;
- no migration combined with tenant middleware retirement or unrelated feature work;
- no compatibility-domain write expansion without explicit review;
- no production or buyer-readiness claim from source inventory alone.

## Closure rule

Issue #1353 closes only after all active consumers are enumerated, compatibility records are migrated or explicitly retained, representative data migration and rollback are proven, reconciliation is zero-unexplained, cross-domain regression is green, and no legacy writer remains active without a documented compatibility deadline.

Until then, compatibility convergence remains open and production remains not approved.
