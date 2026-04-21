$ErrorActionPreference = "Stop"

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Safe-Rename {
    param(
        [string]$OldPath,
        [string]$NewPath
    )
    if ((Test-Path $OldPath) -and (-not (Test-Path $NewPath))) {
        Move-Item -Path $OldPath -Destination $NewPath
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$artifactRoot = Join-Path $repoRoot ("audit-artifacts\crown-phase-system-bootstrap\" + $ts)
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null

$binderRoot = Join-Path $repoRoot "docs\Crown_Master_Binder"
$visionRoot = Join-Path $binderRoot "01_Vision_and_Product"
$canonRoot  = Join-Path $binderRoot "02_Architecture_and_Canons"
$opsRoot    = Join-Path $binderRoot "03_Operations_and_Delivery"
$invRoot    = Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop"
$runRoot    = Join-Path $binderRoot "05_Runbooks_and_Checklists"
$execRoot   = Join-Path $repoRoot "scripts\execution"

New-Item -ItemType Directory -Force -Path $binderRoot,$visionRoot,$canonRoot,$opsRoot,$invRoot,$runRoot,$execRoot | Out-Null

Safe-Rename -OldPath (Join-Path $opsRoot "03_Sprint_Scorecard.csv") -NewPath (Join-Path $opsRoot "03_Phase_Progress_Scorecard.csv")
Safe-Rename -OldPath (Join-Path $opsRoot "07_Weekly_Review_Packet.md") -NewPath (Join-Path $opsRoot "07_Phase_Gate_Review_Packet.md")
Safe-Rename -OldPath (Join-Path $runRoot "05_Week_1_Work_Assignments.md") -NewPath (Join-Path $runRoot "05_Phase_1_Work_Assignments.md")

Write-Utf8File -Path (Join-Path $binderRoot "00_TABLE_OF_CONTENTS.md") -Content @"
# Crown Master Binder

## 1. Vision and Product
- 01_Mission_and_Product_Taxonomy.md
- 02_Phase_One_Scope.md
- 03_Module_Priority_Order.md

## 2. Architecture and Canons
- 01_Crown_Core_Canon.md
- 02_Crown_Modules_Canon.md
- 03_Crown_Addons_Canon.md
- 04_SIS_Canon.md
- 05_Auth_RBAC_Canon.md
- 06_Tenant_Isolation_Canon.md
- 07_Naming_Canon.md
- 08_API_Canon.md
- 09_Frontend_Shell_Canon.md
- 10_Definition_of_Done_Canon.md
- 11_Module_Template.md

## 3. Operations and Delivery
- 01_Team_Ownership.md
- 02_RACI.md
- 03_Phase_Progress_Scorecard.csv
- 04_Risk_Register.csv
- 05_Approval_Gates.md
- 06_Communication_Rules.md
- 07_Phase_Gate_Review_Packet.md
- 08_Git_GitHub_Azure_Rules.md
- 09_Phase_Gate_Register.csv
- 10_Execution_Update_Template.md

## 4. Inventory and Keep-Rewrite-Drop
- 01_Master_Inventory.csv
- 02_Core_Inventory.csv
- 03_Module_Inventory.csv
- 04_Addon_Inventory.csv
- 05_Keep_Rewrite_Drop_Rules.md
- 06_Archive_Purge_Readiness_Checklist.md

## 5. Runbooks and Checklists
- 01_Reset_Runbook.md
- 02_Build_Sequence.md
- 03_Release_Runbook.md
- 04_Environment_Bootstrap_Checklist.md
- 05_Phase_1_Work_Assignments.md
- 06_Phase_1_Inventory_and_Canon_Lock.md
- 07_Phase_2_Classification_and_Approval.md
- 08_Phase_3_Archive_and_Purge_Readiness.md
- 09_Phase_4_Controlled_Purge_and_Clean_Bootstrap.md
- 10_Phase_5_Core_Build.md
- 11_Phase_6_First_Wave_Modules.md
- 12_Phase_7_Hardening_Integration_and_Release_Readiness.md
- 13_Completion_Gate_Master_Checklist.md
"@

Write-Utf8File -Path (Join-Path $opsRoot "03_Phase_Progress_Scorecard.csv") -Content @"
Phase,Stage,Owner,Planned,Completed,Blocked,AtRisk,DecisionNeeded,GateStatus,Notes
Phase 1,Stage A - Draft,Dev 1,0,0,0,0,0,Not Started,
Phase 1,Stage B - Working,Dev 2,0,0,0,0,0,Not Started,
Phase 1,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 1,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 2,Stage A - Draft,Dev 1,0,0,0,0,0,Not Started,
Phase 2,Stage B - Working,Dev 3,0,0,0,0,0,Not Started,
Phase 2,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 2,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 3,Stage A - Draft,Dev 5,0,0,0,0,0,Not Started,
Phase 3,Stage B - Working,Dev 5,0,0,0,0,0,Not Started,
Phase 3,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 3,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 4,Stage A - Draft,Dev 5,0,0,0,0,0,Not Started,
Phase 4,Stage B - Working,Dev 5,0,0,0,0,0,Not Started,
Phase 4,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 4,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 5,Stage A - Draft,Dev 1,0,0,0,0,0,Not Started,
Phase 5,Stage B - Working,Dev 2,0,0,0,0,0,Not Started,
Phase 5,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 5,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 6,Stage A - Draft,Dev 3,0,0,0,0,0,Not Started,
Phase 6,Stage B - Working,Dev 4,0,0,0,0,0,Not Started,
Phase 6,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 6,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
Phase 7,Stage A - Draft,Dev 5,0,0,0,0,0,Not Started,
Phase 7,Stage B - Working,Dev 5,0,0,0,0,0,Not Started,
Phase 7,Stage C - Evidence Complete,Dev 5,0,0,0,0,0,Not Started,
Phase 7,Stage D - Gate Review,TC,0,0,0,0,0,Not Started,
"@

Write-Utf8File -Path (Join-Path $opsRoot "04_Risk_Register.csv") -Content @"
RiskID,Phase,Risk,Owner,Severity,Probability,Mitigation,GateImpact,Status,Notes
R-001,Phase 1,Inventory incomplete before classification,Dev 5,High,Medium,No classification until master inventory is materially complete,Blocks Gate 1,Open,
R-002,Phase 2,Shadow truth reintroduced by modules,Dev 1,High,Medium,Enforce core truth and API canon,Blocks Gate 2,Open,
R-003,Phase 3,Archive package incomplete before purge readiness,Dev 5,High,Medium,No purge readiness approval without restore confidence,Blocks Gate 3,Open,
R-004,Phase 4,Deletion occurs before sign-off,TC,High,Low,Gate approval required before any destructive action,Blocks Gate 4,Open,
R-005,Phase 5,Core contracts drift during build,Dev 1,High,Medium,Canon and contract review required for every merge,Blocks Gate 5,Open,
R-006,Phase 6,Module workflows bypass core contracts,Dev 3,High,Medium,Require integration testing and owner review,Blocks Gate 6,Open,
R-007,Phase 7,Release evidence incomplete despite green screens,Dev 5,High,Medium,Definition of Done and release runbook required,Blocks Gate 7,Open,
"@

Write-Utf8File -Path (Join-Path $opsRoot "05_Approval_Gates.md") -Content @"
# Approval Gates

## Status levels
- Draft
- Working
- Evidence Complete
- Gate Review
- Approved
- Rework Required

## Gate owners
- Gate 1 approval: TC
- Gate 2 approval: TC
- Gate 3 approval: Dev 5 + TC
- Gate 4 approval: Dev 5 + TC
- Gate 5 approval: Dev 1 + TC
- Gate 6 approval: Dev 3 + Dev 5 + TC
- Gate 7 approval: Dev 5 + TC

## Rule
Nothing is treated as complete because files exist.
It is complete only when the proper gate marks it approved.
"@

Write-Utf8File -Path (Join-Path $opsRoot "06_Communication_Rules.md") -Content @"
# Communication Rules

## Execution updates
- use one execution update channel or document
- blockers escalate immediately
- decisions are logged in the binder, not lost in chat
- all updates are tied to phase, stage, and gate status

## Interrupt rules
- interrupt TC for scope, canon, gate, or release go/no-go decisions
- do not interrupt TC for implementation details already governed by canon

## Rule
Chat is not the system of record.
The binder is.
"@

Write-Utf8File -Path (Join-Path $opsRoot "07_Phase_Gate_Review_Packet.md") -Content @"
# Phase Gate Review Packet

## Include
- phase summary
- current stage status
- decisions made
- blockers still open
- risks added
- outputs completed
- binder sections advanced
- gate recommendation
- approved next phase or required rework
"@

Write-Utf8File -Path (Join-Path $opsRoot "09_Phase_Gate_Register.csv") -Content @"
GateID,Phase,GateName,Owner,EntryCriteria,ExitCriteria,Status,DecisionDate,DecisionBy,Notes
G-001,Phase 1,Inventory and Canon Lock,TC,Inventory underway and canon drafts started,Inventory materially complete and canon drafts ready,Not Started,,,
G-002,Phase 2,Classification and Approval,TC,Gate 1 approved,Keep/Rewrite/Drop and canon approvals complete,Not Started,,,
G-003,Phase 3,Archive and Purge Readiness,Dev 5 + TC,Gate 2 approved,Archive packages and restore confidence complete,Not Started,,,
G-004,Phase 4,Controlled Purge and Clean Bootstrap,Dev 5 + TC,Gate 3 approved,Controlled purge complete and clean bootstrap approved,Not Started,,,
G-005,Phase 5,Core Build,Dev 1 + TC,Gate 4 approved,Core truth and contracts stable with evidence,Not Started,,,
G-006,Phase 6,First-Wave Modules,Dev 3 + Dev 5 + TC,Gate 5 approved,Admissions/Re-enrollment/Billing/Portals integrated and validated,Not Started,,,
G-007,Phase 7,Hardening and Release Readiness,Dev 5 + TC,Gate 6 approved,Release evidence complete and definition of done satisfied,Not Started,,,
"@

Write-Utf8File -Path (Join-Path $opsRoot "10_Execution_Update_Template.md") -Content @"
# Execution Update Template

## Phase
## Stage
## Owner
## Outputs completed
## Outputs in progress
## Blockers
## Risks
## Decisions needed
## Gate impact
## Next controlled action
"@

Write-Utf8File -Path (Join-Path $runRoot "01_Reset_Runbook.md") -Content @"
# Reset Runbook

## Sequence
1. inventory
2. canon lock
3. classify
4. archive
5. purge readiness
6. controlled purge
7. clean bootstrap
8. rebuild
9. harden
10. release readiness

## Rule
Do not wipe first and then think.
Think first, archive second, wipe third.
"@

Write-Utf8File -Path (Join-Path $runRoot "02_Build_Sequence.md") -Content @"
# Build Sequence

## Phase 1 - Inventory and Canon Lock
- inventory everything
- classify nothing yet unless obvious
- no deletion
- lock naming and structure rules

## Phase 2 - Classification and Approval
- rewrite and approve canons
- classify keep/rewrite/drop
- approve phase-one scope
- confirm product taxonomy

## Phase 3 - Archive and Purge Readiness
- produce archive packages
- verify archive completeness
- prepare deletion checklist
- confirm restore confidence

## Phase 4 - Controlled Purge and Clean Bootstrap
- controlled purge
- clean bootstrap
- confirm approved structure only
- begin core build

## Phase 5 - Core Build
- auth
- RBAC
- tenant isolation
- audit
- canonical SIS truth
- shared backend contracts
- shared frontend shell

## Phase 6 - First-Wave Modules
- admissions
- re-enrollment
- billing / payments
- communications + portals

## Phase 7 - Hardening, Integration, Release Readiness
- test hardening
- integration validation
- role and tenant proofs
- release evidence
- go/no-go

## Control rule
No movement to the next phase without gate approval.
"@

Write-Utf8File -Path (Join-Path $runRoot "03_Release_Runbook.md") -Content @"
# Release Runbook

## Rule
No release is complete because a page renders.

## Release prerequisites
- Gate 7 approved
- Definition of Done passed
- permissions enforced
- tenant rules enforced
- tests passed
- release evidence updated
- control-center status green

## Release checkpoints
- preflight
- deploy
- migration
- smoke tests
- go/no-go
- hypercare
"@

Write-Utf8File -Path (Join-Path $runRoot "04_Environment_Bootstrap_Checklist.md") -Content @"
# Environment Bootstrap Checklist

- [ ] clean repo structure approved
- [ ] clean frontend shell approved
- [ ] clean backend core structure approved
- [ ] naming canon approved
- [ ] Git / branch rules approved
- [ ] release runbook approved
- [ ] first core targets assigned
- [ ] controlled purge complete or not required
- [ ] archive package verified
- [ ] restore confidence verified
"@

Write-Utf8File -Path (Join-Path $runRoot "05_Phase_1_Work_Assignments.md") -Content @"
# Phase 1 Work Assignments

## Objective
Complete inventory and lock governing canons before classification, purge, or rebuild.

## Dev 1
- inventory backend platform/auth/tenant code
- draft platform architecture map

## Dev 2
- inventory data models and schema
- create entity list and dependency map

## Dev 3
- inventory operations modules and workflows
- identify duplicates and dead ends

## Dev 4
- inventory frontend pages, routes, shells, widgets, components

## Dev 5
- inventory repos, branches, PRs, workflows, releases
- inventory Azure/resource/env/deploy truth
- maintain master inventory sheet

## TC
- define one-page business goal of the reset
- approve binder structure
- approve initial product taxonomy

## Exit gate
Phase 1 is complete only when inventory is materially complete and canon drafts are ready for approval.
"@

Write-Utf8File -Path (Join-Path $runRoot "06_Phase_1_Inventory_and_Canon_Lock.md") -Content @"
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
"@

Write-Utf8File -Path (Join-Path $runRoot "07_Phase_2_Classification_and_Approval.md") -Content @"
# Phase 2 - Classification and Approval

## Purpose
Classify every relevant artifact and formally approve the governing model.

## Scope
- keep/rewrite/drop classification
- core/module/add-on classification
- canon approval
- phase-one scope approval
- build-order approval

## Required outputs
- keep/rewrite/drop decisions populated where possible
- core/module/add-on assignments corrected and approved
- approved Crown Core Canon
- approved Crown Modules Canon
- approved Crown Add-ons Canon
- approved Naming Canon
- approved API Canon
- approved Frontend Shell Canon
- approved Definition of Done Canon

## Work lanes

### Dev 1
- approve platform and architecture classifications
- resolve platform ownership conflicts
- finalize auth/RBAC/tenant/API authority

### Dev 2
- approve SIS entity classifications
- resolve duplicate student/family/enrollment truth
- finalize canonical SIS boundaries

### Dev 3
- approve module classifications
- confirm first-wave and second-wave module boundaries
- remove module attempts to own core truth

### Dev 4
- approve frontend keep/rewrite/drop calls
- confirm shared shell, route, and component standards
- eliminate UI drift categories

### Dev 5
- maintain approval ledger
- capture unresolved items requiring TC decision
- prepare Gate 2 evidence package

### TC
- approve product taxonomy
- approve phase-one scope
- approve final tie-breaks on classification and authority

## Hard stops
- no purge readiness sign-off
- no clean bootstrap
- no phase-five build work until phase-two approvals are complete

## Entry criteria
- Gate 1 approved

## Exit criteria
- classifications are materially complete
- authority canons are approved
- build order is approved
- Gate 2 review package is ready

## Evidence pack
- updated inventory CSVs with classification values
- approval record
- final canon files
- unresolved exceptions list
- Gate 2 review packet
"@

Write-Utf8File -Path (Join-Path $runRoot "08_Phase_3_Archive_and_Purge_Readiness.md") -Content @"
# Phase 3 - Archive and Purge Readiness

## Purpose
Produce preservation packages and prove that controlled deletion would not destroy necessary truth.

## Scope
- code archive packages
- workflow archive packages
- documentation archive packages
- environment and config archive packages
- schema and restore-confidence proof
- purge checklist completion

## Required outputs
- archive package for repo and key branches
- archive package for workflows and release records
- archive package for docs and governance artifacts
- archive package for environment truth and deployment references
- archive package for schema and data-model evidence
- completed archive/purge readiness checklist

## Work lanes

### Dev 1
- verify platform archive completeness
- verify architecture authority is preserved

### Dev 2
- verify schema and data-model preservation
- confirm restore confidence for SIS truth

### Dev 3
- verify operations workflow preservation
- confirm module business rules are preserved

### Dev 4
- verify frontend structure and UI authority preservation
- confirm route and shell evidence archived

### Dev 5
- assemble the master archive package
- maintain the purge readiness checklist
- verify restore confidence and environment dependency maps
- prepare Gate 3 evidence package

### TC
- approve whether purge readiness is sufficient
- block any destructive action if preservation is incomplete

## Hard stops
- no destructive action without Gate 3 approval
- no "we can rebuild it later" assumptions
- no purge based on memory alone

## Entry criteria
- Gate 2 approved

## Exit criteria
- archive packages exist and are verified
- purge readiness checklist is complete
- restore confidence is documented
- Gate 3 review package is ready

## Evidence pack
- archive package index
- restore confidence notes
- purge readiness checklist
- risk updates
- Gate 3 review packet
"@

Write-Utf8File -Path (Join-Path $runRoot "09_Phase_4_Controlled_Purge_and_Clean_Bootstrap.md") -Content @"
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
"@

Write-Utf8File -Path (Join-Path $runRoot "10_Phase_5_Core_Build.md") -Content @"
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
"@

Write-Utf8File -Path (Join-Path $runRoot "11_Phase_6_First_Wave_Modules.md") -Content @"
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
"@

Write-Utf8File -Path (Join-Path $runRoot "12_Phase_7_Hardening_Integration_and_Release_Readiness.md") -Content @"
# Phase 7 - Hardening, Integration, and Release Readiness

## Purpose
Prove that Crown is not just built, but controlled, integrated, and release-ready.

## Scope
- defect reduction
- regression testing
- permission hardening
- tenant hardening
- release evidence
- environment proof
- demo and pilot stability
- go/no-go decision

## Required outputs
- passing regression set
- role and tenant proof pack
- release runbook evidence
- bug and blocker disposition
- environment validation
- release candidate status
- go/no-go recommendation

## Work lanes

### Dev 1
- architecture review
- technical debt reduction
- contract integrity checks

### Dev 2
- data integrity review
- migration review
- schema safety validation

### Dev 3
- workflow edge-case cleanup
- module completeness validation

### Dev 4
- UI consistency cleanup
- accessibility and usability cleanup
- shell and module polish

### Dev 5
- full regression
- proof pack production
- release certification package
- Gate 7 evidence package

### TC
- final product fit acceptance
- final release priority decision
- go/no-go decision

## Hard stops
- no release because pages look good
- no release without evidence
- no release with unresolved critical truth, permission, or tenant failures

## Entry criteria
- Gate 6 approved

## Exit criteria
- release evidence is complete
- definition of done is satisfied for active release scope
- go/no-go decision is made
- Gate 7 is approved

## Evidence pack
- regression results
- proof pack
- release checklist
- blocker disposition
- go/no-go record
- Gate 7 review packet
"@

Write-Utf8File -Path (Join-Path $runRoot "13_Completion_Gate_Master_Checklist.md") -Content @"
# Completion Gate Master Checklist

## Gate 1 - Inventory and Canon Lock
- [ ] master inventory materially complete
- [ ] lane inventories materially complete
- [ ] canon drafts created
- [ ] risk register updated
- [ ] Gate 1 review packet complete

## Gate 2 - Classification and Approval
- [ ] keep/rewrite/drop materially complete
- [ ] core/module/add-on classification materially complete
- [ ] governing canons approved
- [ ] build order approved
- [ ] Gate 2 review packet complete

## Gate 3 - Archive and Purge Readiness
- [ ] archive package complete
- [ ] restore confidence verified
- [ ] archive/purge readiness checklist complete
- [ ] Gate 3 review packet complete

## Gate 4 - Controlled Purge and Clean Bootstrap
- [ ] purge scope approved
- [ ] purge ledger complete
- [ ] clean bootstrap complete
- [ ] approved structure confirmed
- [ ] Gate 4 review packet complete

## Gate 5 - Core Build
- [ ] auth/RBAC/tenant stable
- [ ] canonical SIS truth stable
- [ ] shared shell stable
- [ ] core tests passing
- [ ] Gate 5 review packet complete

## Gate 6 - First-Wave Modules
- [ ] admissions complete
- [ ] re-enrollment complete
- [ ] billing complete
- [ ] portals validated
- [ ] integration tests passing
- [ ] Gate 6 review packet complete

## Gate 7 - Hardening and Release Readiness
- [ ] regression passing
- [ ] proof pack complete
- [ ] release runbook satisfied
- [ ] go/no-go decision recorded
- [ ] Gate 7 approved
"@

Write-Utf8File -Path (Join-Path $execRoot "63_open_crown_phase_system.ps1") -Content @"
`$ErrorActionPreference = "Stop"

code .\docs\Crown_Master_Binder\00_TABLE_OF_CONTENTS.md
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\05_Approval_Gates.md
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\07_Phase_Gate_Review_Packet.md
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\02_Build_Sequence.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\06_Phase_1_Inventory_and_Canon_Lock.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\07_Phase_2_Classification_and_Approval.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\08_Phase_3_Archive_and_Purge_Readiness.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\09_Phase_4_Controlled_Purge_and_Clean_Bootstrap.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\10_Phase_5_Core_Build.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\11_Phase_6_First_Wave_Modules.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\12_Phase_7_Hardening_Integration_and_Release_Readiness.md
code .\docs\Crown_Master_Binder\05_Runbooks_and_Checklists\13_Completion_Gate_Master_Checklist.md
"@

Write-Utf8File -Path (Join-Path $execRoot "64_phase_status_seed.ps1") -Content @"
`$ErrorActionPreference = "Stop"

`$score = ".\docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv"
`$gate  = ".\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv"

if (Test-Path `$score) { Import-Csv `$score | Format-Table -AutoSize }
if (Test-Path `$gate)  { Import-Csv `$gate  | Format-Table -AutoSize }
"@

Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content @"
# Crown Complete Phase System Bootstrap Summary

## Model
- Phase = major body of work
- Stage = checkpoint inside a phase
- Gate = approval to proceed

## Files created or rewritten
- docs/Crown_Master_Binder/00_TABLE_OF_CONTENTS.md
- docs/Crown_Master_Binder/03_Operations_and_Delivery/03_Phase_Progress_Scorecard.csv
- docs/Crown_Master_Binder/03_Operations_and_Delivery/04_Risk_Register.csv
- docs/Crown_Master_Binder/03_Operations_and_Delivery/05_Approval_Gates.md
- docs/Crown_Master_Binder/03_Operations_and_Delivery/06_Communication_Rules.md
- docs/Crown_Master_Binder/03_Operations_and_Delivery/07_Phase_Gate_Review_Packet.md
- docs/Crown_Master_Binder/03_Operations_and_Delivery/09_Phase_Gate_Register.csv
- docs/Crown_Master_Binder/03_Operations_and_Delivery/10_Execution_Update_Template.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/01_Reset_Runbook.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/02_Build_Sequence.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/03_Release_Runbook.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/04_Environment_Bootstrap_Checklist.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/05_Phase_1_Work_Assignments.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/06_Phase_1_Inventory_and_Canon_Lock.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/07_Phase_2_Classification_and_Approval.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/08_Phase_3_Archive_and_Purge_Readiness.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/09_Phase_4_Controlled_Purge_and_Clean_Bootstrap.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/10_Phase_5_Core_Build.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/11_Phase_6_First_Wave_Modules.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/12_Phase_7_Hardening_Integration_and_Release_Readiness.md
- docs/Crown_Master_Binder/05_Runbooks_and_Checklists/13_Completion_Gate_Master_Checklist.md
- scripts/execution/63_open_crown_phase_system.ps1
- scripts/execution/64_phase_status_seed.ps1

## Rule
No active operating document should use day, week, or sprint framing.
All control is phase, stage, and gate based.
"@

Write-Host ""
Write-Host "DONE"
Write-Host "Repo root: $repoRoot"
Write-Host "Binder root: $binderRoot"
Write-Host "Summary: $(Join-Path $artifactRoot 'SUMMARY.md')"
Write-Host ""
Write-Host "Open next:"
Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\63_open_crown_phase_system.ps1"
