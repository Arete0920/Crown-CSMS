# Phase 4 - Controlled Purge and Clean Bootstrap

## Purpose
Perform only approved destructive cleanup and establish the clean operating structure for the rebuild.

## Scope
- controlled purge of approved stale assets
- environment cleanup where approved
- repo cleanup where approved
- approved bootstrap of clean structure
- no uncontrolled redesign

## Required outputs
- purge log
- deleted or archived item ledger
- clean bootstrap structure
- approved repo structure
- approved environment bootstrap state
- updated inventory reflecting purge outcomes

## Work lanes

### Dev 1
- protect core architectural structure during cleanup
- scaffold approved backend structure only

### Dev 2
- protect canonical data-model and schema direction
- scaffold approved SIS structure only

### Dev 3
- protect first-wave module boundaries
- ensure module scaffolds do not bypass core truth

### Dev 4
- scaffold shared frontend shell and component structure
- remove unapproved frontend drift items

### Dev 5
- lead controlled purge execution
- maintain purge ledger and rollback notes
- verify that every destructive action matches approved decisions
- prepare Gate 4 evidence package

### TC
- approve purge scope before action
- approve clean bootstrap after action

## Hard stops
- no destructive action outside approved decisions
- no rebuild outside approved structure
- no importing junk back into the clean bootstrap

## Entry criteria
- Gate 3 approved

## Exit criteria
- approved purge items handled
- clean bootstrap created
- purge ledger and rollback notes complete
- Gate 4 review package is ready

## Evidence pack
- purge ledger
- before and after inventory delta
- clean structure map
- rollback notes
- Gate 4 review packet
