# Phase 5 - Core Build

## Purpose
Build the non-negotiable Crown foundation and system-of-record truth.

## Scope
- auth
- RBAC
- tenant isolation
- audit logging
- shared backend contracts
- shared error handling
- shared frontend shell
- canonical SIS truth
- core APIs
- core validations
- core tests

## Required outputs
- stable auth and RBAC rules
- stable tenant enforcement
- stable canonical SIS entities
- stable shared API contracts
- stable shared frontend shell
- passing core test set
- updated Definition of Done evidence

## Work lanes

### Dev 1
- own auth, RBAC, tenant, audit, backend standards, contract reviews
- prevent module code from defining core truth

### Dev 2
- own SIS entities, lifecycle rules, migrations, validation rules, and canonical APIs
- resolve duplicate student, guardian, household, staff, enrollment, and academic truth

### Dev 3
- own business-service integration points that will later support modules
- do not build module-specific bypasses into core

### Dev 4
- own shell, navigation, shared forms, shared tables, shared layouts, and role patterns
- no dashboard-first shortcuts

### Dev 5
- own integration test baseline, contract tests, tenant tests, and environment proof
- prepare Gate 5 evidence package

### TC
- approve core boundaries
- approve what is in or out of core
- reject scope bloat

## Hard stops
- no phase-six module delivery claims
- no dashboard vanity work
- no module-owned alternate truth

## Entry criteria
- Gate 4 approved

## Exit criteria
- core contracts are stable
- shared shell is stable
- core truth is test-validated
- Gate 5 review package is ready

## Evidence pack
- core API map
- core entity map
- role and tenant proof
- core test results
- Gate 5 review packet
