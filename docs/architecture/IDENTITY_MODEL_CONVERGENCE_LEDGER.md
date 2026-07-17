# CROWN Identity Model Convergence Ledger

Status: execution inventory under #1353  
Migration strategy: expand-contract; no destructive rename or table collapse

## Purpose

Define the evidence required to reconcile CROWN's three verified household, guardian/person, and student model sets without silent data loss, cross-tenant merging, broken portal access, or downstream financial and academic corruption.

## Verified model sets

### 1. `core.models`

Relational operational spine with School foreign keys and downstream dependencies including user accounts, enrollment, tuition, ledger, attendance, gradebook, reporting, and portal behavior.

### 2. `households.models`

Lightweight household, guardian, and student tables using bare `school_id` UUID fields and simplified attributes.

### 3. `crown_api.models_households`

Person-centered structure with Household, HouseholdMember role relationships, and a Student person profile. Tenant ownership is not explicit at the household level and must be resolved before canonical consideration.

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

## Canonical decision criteria

A model set may become canonical only when it demonstrates:

1. explicit tenant ownership and fail-closed scoping;
2. sufficient identity and relationship semantics for all current product domains;
3. stable external and portal identity mapping;
4. referential integrity for financial, academic, and operational dependencies;
5. deterministic migration mapping from both non-canonical sets;
6. compatibility strategy for active APIs and reports;
7. rollback without losing writes accepted during migration.

Current relational evidence favors `core.models` as the dependency anchor, but this ledger does not declare a final canonical model before row-level and consumer-level proof.

## Expand-contract sequence

1. Freeze the dependency and row-count baseline.
2. Declare canonical identity keys and tenant invariants in an accepted ADR.
3. Add mapping tables or deterministic mapping functions without deleting legacy data.
4. Rehearse migration on a production-shaped non-production copy.
5. Backfill tenant by tenant with reconciliation totals.
6. Add compatibility reads or adapters where required.
7. Move writers by bounded domain, beginning with the lowest side-effect surface.
8. Prove read equivalence and permission equivalence.
9. Observe production-shaped behavior for a defined period.
10. Retire legacy writers, then readers, then tables only after explicit disposition of every unmatched record.

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
- no production or buyer-readiness claim from source inventory alone.

## Closure rule

Issue #1353 closes only after canonical identity authority is accepted, all consumers are migrated or explicitly retained, representative data migration and rollback are proven, reconciliation is zero-unexplained, cross-domain regression is green, and no legacy writer remains active without a documented compatibility deadline.
