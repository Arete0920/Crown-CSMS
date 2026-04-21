# Phase 6 - First-Wave Modules

## Purpose
Build the first operational systems that make Crown usable as a real school platform.

## Scope
- admissions
- re-enrollment
- billing / tuition / payments
- communications
- parent portal
- teacher portal
- administrator portal

## Required outputs
- applicant-to-enrolled workflow
- re-enrollment workflow
- billing obligations, charges, payments, and balances
- communications basics
- role-based portals backed by real contracts
- module tests and integration tests
- no shadow truth

## Work lanes

### Dev 1
- enforce permission, tenant, audit, and contract discipline for all modules

### Dev 2
- enforce SIS linkages and canonical references for all module data interactions

### Dev 3
- own module workflows, business services, and bounded module contracts

### Dev 4
- own module UX using shared shell and components only
- no duplicate route registries
- no fake dashboards disconnected from working data

### Dev 5
- own cross-module testing, regression, release discipline, and Gate 6 evidence package

### TC
- approve module boundaries and commercial priority
- reject non-priority expansion

## Hard stops
- no second-wave expansion until first-wave modules are integrated and validated
- no module may own canonical core truth
- no module may bypass auth, RBAC, tenant, audit, or shared contracts

## Entry criteria
- Gate 5 approved

## Exit criteria
- first-wave modules work end-to-end
- portals consume real module and core data
- integration tests pass
- Gate 6 review package is ready

## Evidence pack
- module workflow maps
- integration test results
- permission and tenant proofs
- portal validation notes
- Gate 6 review packet
