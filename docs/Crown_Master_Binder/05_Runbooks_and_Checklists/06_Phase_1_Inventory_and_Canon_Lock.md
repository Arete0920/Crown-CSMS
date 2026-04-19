# Phase 1 - Inventory and Canon Lock

## Purpose
Create full operational truth before any classification, purge, or rebuild action.

## Scope
- repo inventory
- branch and PR inventory
- workflow inventory
- infrastructure inventory
- data-model inventory
- frontend inventory
- module and add-on inventory
- canon draft creation

## Required outputs
- master inventory populated
- core inventory populated
- module inventory populated
- add-on inventory populated
- initial canon drafts ready
- lane-level inventory summaries
- top risks identified

## Work lanes

### Dev 1 - Platform
- inventory auth, RBAC, tenant, audit, API, security, middleware, shared backend contracts
- identify platform duplicates, stale code, and drift points
- draft platform architecture authority notes

### Dev 2 - SIS and Data
- inventory students, households, guardians, staff, enrollment, attendance, grades, transcripts, academic structures
- document lifecycle rules and current schema truth
- identify shadow truth and duplicate entities

### Dev 3 - Modules and Workflows
- inventory admissions, re-enrollment, billing, payments, communications, portals, and second-wave modules
- identify module overlap, dead ends, and bypasses of core truth
- map module entry and exit points

### Dev 4 - Frontend
- inventory routes, pages, shells, components, widgets, sidebars, forms, tables, and layout patterns
- identify duplicate route registries and dashboard-first drift
- map role-view structure and frontend inconsistencies

### Dev 5 - Control, Delivery, Environments
- inventory repos, branches, PRs, workflows, releases, evidence packs, environments, configs, and deployment truth
- maintain the master inventory and gate register
- capture environment risks and restore dependencies

### TC
- approve binder structure
- approve taxonomy direction
- approve what counts as authority and what counts as draft only

## Hard stops
- no deletion
- no active purge
- no "temporary" rebuild outside the binder structure
- no classification without inventory evidence

## Entry criteria
- binder structure exists
- owners assigned
- inventory sheets available

## Exit criteria
- inventories are materially complete
- canon drafts exist for core decision areas
- risks and blockers are documented
- Gate 1 review package is ready

## Evidence pack
- updated inventory CSVs
- lane summaries
- canon draft list
- risk register updates
- Gate 1 review packet
