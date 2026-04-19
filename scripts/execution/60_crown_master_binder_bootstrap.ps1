param(
    [switch]$OpenFiles
)

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

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$artifactRoot = Join-Path $repoRoot ("audit-artifacts\crown-master-binder-bootstrap\" + $ts)
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null

$binderRoot = Join-Path $repoRoot "docs\Crown_Master_Binder"
New-Item -ItemType Directory -Force -Path $binderRoot | Out-Null

# --------------------------------------------------
# ROOT TOC
# --------------------------------------------------
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
- 03_Sprint_Scorecard.csv
- 04_Risk_Register.csv
- 05_Approval_Gates.md
- 06_Communication_Rules.md
- 07_Weekly_Review_Packet.md
- 08_Git_GitHub_Azure_Rules.md

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
- 05_Week_1_Work_Assignments.md
"@

# --------------------------------------------------
# 1. VISION AND PRODUCT
# --------------------------------------------------
Write-Utf8File -Path (Join-Path $binderRoot "01_Vision_and_Product\01_Mission_and_Product_Taxonomy.md") -Content @"
# Mission and Product Taxonomy

## Mission
Crown is a Christ-centered school operations platform built on a clean layered model:
- Core
- Modules
- Add-ons

## Official product structure

### Core
Core is foundation and truth.
Core owns:
- auth
- RBAC
- tenant isolation
- audit logging
- shared backend contracts
- shared API rules
- shared frontend shell standards
- canonical student/family/staff truth
- canonical school/year/term/enrollment truth

### Modules
Modules run major school operations and must plug into Core truth.
First-wave modules:
- Admissions
- Re-enrollment
- Billing / Tuition / Payments
- Communications + Portals

Second-wave modules:
- Transportation
- Food Service
- Nurse Office
- Athletics / Activities
- Board Dashboards

### Add-ons
Add-ons integrate cleanly and may stand alone, but they do not own Core truth.
Examples:
- Spiritual Life
- Service / Outreach
- PD Hub
- Compass
- other differentiated extensions

## Product rule
Core owns truth.
Modules run school operations.
Add-ons integrate cleanly.
Nothing may create shadow truth.
"@

Write-Utf8File -Path (Join-Path $binderRoot "01_Vision_and_Product\02_Phase_One_Scope.md") -Content @"
# Phase One Scope

## Included now
- secure login
- tenant isolation
- role-based access
- student/family/staff master records
- admissions pipeline
- enrollment / re-enrollment
- tuition/fees/payments core
- announcements/messages
- basic admin, parent, teacher views

## Explicit non-goals for phase one
- duplicate dashboard experiments
- disconnected route registries
- ungoverned add-on sprawl
- cloud/environment sprawl before structure is stable
- demo-only pages with no stable data model or permissions

## Success condition
Phase one is complete only when Core and first-wave Modules are production-quality under the Definition of Done.
"@

Write-Utf8File -Path (Join-Path $binderRoot "01_Vision_and_Product\03_Module_Priority_Order.md") -Content @"
# Module Priority Order

## Build order
1. Core Platform + SIS truth
2. Admissions
3. Re-enrollment
4. Billing / Tuition / Payments
5. Communications + Portals
6. Second-wave modules
7. Add-ons

## Rule
No dashboard-first development.
No module build before Core truth, permission rules, and API contracts are defined.
"@

# --------------------------------------------------
# 2. ARCHITECTURE AND CANONS
# --------------------------------------------------
Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\01_Crown_Core_Canon.md") -Content @"
# Crown Core Canon

## Purpose
Define the non-negotiable platform foundation.

## Core responsibilities
- authentication
- RBAC
- tenant enforcement
- audit/event framework
- shared error handling
- shared backend patterns
- shared frontend shell rules
- release discipline

## Non-negotiables
- Core owns truth
- Core contracts must be stable before modules build against them
- no module may bypass tenant or permission enforcement
- no duplicate source of truth for identity or enrollment
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\02_Crown_Modules_Canon.md") -Content @"
# Crown Modules Canon

## Rule
Modules consume Core truth and extend operations; they do not replace Core truth.

## Module responsibilities
- implement major school business workflows
- use canonical records from Core
- expose stable module APIs
- comply with permission, tenant, validation, and audit rules

## Module constraints
- no shadow entities
- no hidden route registries
- no module-owned alternate auth model
- no bypassing shared contracts
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\03_Crown_Addons_Canon.md") -Content @"
# Crown Add-ons Canon

## Rule
Add-ons are integrated but not allowed to redefine Core or Module truth.

## Requirements
- clear business purpose
- explicit integration points
- explicit permissions
- explicit audit rules where required
- no ownership of canonical SIS/Core entities
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\04_SIS_Canon.md") -Content @"
# SIS Canon

## Define the SIS by truth and workflow, not by screens

## Core entities
- student
- guardian
- household
- staff
- academic year
- term
- enrollment
- courses
- sections
- rosters
- attendance
- grades
- transcript/report records
- discipline / student-care summary

## Core workflows
- applicant to enrolled
- student record creation
- annual rollover
- section assignment
- attendance posting
- grade posting
- report card generation
- withdrawal / transfer / graduation

## Order of work
1. domain map
2. data model
3. lifecycle/status rules
4. permission matrix
5. API contract
6. basic admin screens
7. role-specific views
8. dashboards
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\05_Auth_RBAC_Canon.md") -Content @"
# Auth / RBAC Canon

## Purpose
Define role-based access and approval boundaries.

## Rules
- every endpoint enforces role and tenant
- every screen enforces role and tenant
- permissions are defined before UI is called complete
- no hidden bypass path
- admin, registrar, teacher, parent, student, finance, admissions roles are explicitly mapped
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\06_Tenant_Isolation_Canon.md") -Content @"
# Tenant Isolation Canon

## Rule
No data, route, or service may cross tenant boundaries unless explicitly designed and approved.

## Requirements
- school context enforced
- tenant-aware queries only
- tenant-safe exports only
- tenant-safe jobs and reports only
- verification tests required
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\07_Naming_Canon.md") -Content @"
# Naming Canon

## Purpose
Prevent drift and ambiguity.

## Standards
- one canonical module name
- one canonical entity name
- one canonical file-location rule
- one canonical route naming rule
- one canonical API naming rule
- no mystery abbreviations
- no temporary names that become permanent

## Required columns for every controlled inventory item
- Item
- Lane
- Category
- Owner
- Status
- Keep/Rewrite/Drop
- Final Decision
- Notes
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\08_API_Canon.md") -Content @"
# API Canon

## Rules
- documented endpoint purpose
- request/response defined
- permission rule defined
- tenant rule defined
- validation defined
- error behavior defined
- audit rule defined where required
- integration points documented
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\09_Frontend_Shell_Canon.md") -Content @"
# Frontend Shell Canon

## Rules
- one source of truth for navigation
- one route registry
- one shared shell
- one component standard
- no mystery sidebars
- no dashboard-first development
- no duplicate route configs
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\10_Definition_of_Done_Canon.md") -Content @"
# Definition of Done Canon

A module is not done because a page renders.

A module is done only when:
- business purpose defined
- user roles defined
- domain model defined
- permissions enforced
- tenant rules enforced
- backend endpoints documented
- frontend screens mapped
- validations defined
- audit rules defined where required
- test cases defined
- tests passing
- integration points validated
- demo flow works
- release/readiness evidence updated where required
"@

Write-Utf8File -Path (Join-Path $binderRoot "02_Architecture_and_Canons\11_Module_Template.md") -Content @"
# Canonical Module Template

## Business purpose
## User roles
## Domain model
## Permissions
## Backend endpoints
## Frontend screens
## Validations
## Audit rules
## Test cases
## Done definition
"@

# --------------------------------------------------
# 3. OPERATIONS AND DELIVERY
# --------------------------------------------------
Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\01_Team_Ownership.md") -Content @"
# Team Ownership

## Dev 1 — Core Platform Lead
Owns:
- auth
- RBAC
- tenant isolation
- audit
- platform contracts
- architecture guardrails

## Dev 2 — SIS Core Lead
Owns:
- SIS entities
- data model
- lifecycle rules
- canonical record APIs

## Dev 3 — Operations Modules Lead
Owns first-wave modules:
- Admissions
- Re-enrollment
- Billing / Tuition / Payments

## Dev 4 — Frontend / UX Lead
Owns:
- shared shell
- shared components
- route/nav standards
- UI consistency

## Dev 5 — Integration / QA / Release Lead
Owns:
- contract testing
- tenant/permission testing
- integration
- release discipline

## TC — Product owner / final authority
Owns:
- product boundaries
- canon approval
- build priority
- scope approval
- final acceptance
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\02_RACI.md") -Content @"
# RACI

| Area | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Crown Core Canon | Dev 1 | TC | Dev 2, Dev 5 | Team |
| SIS Canon | Dev 2 | TC | Dev 1, Dev 3 | Team |
| Modules Canon | Dev 3 | TC | Dev 1, Dev 4 | Team |
| Add-ons Canon | Dev 3 | TC | Dev 1, Dev 4 | Team |
| Frontend Shell Canon | Dev 4 | TC | Dev 1, Dev 3 | Team |
| API Canon | Dev 1 | TC | Dev 2, Dev 5 | Team |
| Definition of Done | Dev 5 | TC | Dev 1-4 | Team |
| Master Inventory | Dev 5 | TC | Dev 1-4 | Team |
| Archive / Purge Checklist | Dev 5 | TC | Dev 1-4 | Team |
| Release Runbook | Dev 5 | TC | Dev 1-4 | Team |
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\03_Sprint_Scorecard.csv") -Content @"
Date,Sprint,Owner,Planned,Completed,Blocked,AtRisk,DecisionNeeded,Notes
,,,0,0,0,0,0,
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\04_Risk_Register.csv") -Content @"
RiskID,Risk,Owner,Severity,Probability,Mitigation,NextReviewDate,Status,Notes
R-001,Inventory incomplete before deletion,Dev 5,High,Medium,No deletion until inventories and archive are complete,,Open,
R-002,Shadow truth reintroduced by modules,Dev 1,High,Medium,Enforce Core truth and API canon,,Open,
R-003,Dashboard-first drift,Dev 4,Medium,Medium,Follow build order and Definition of Done,,Open,
R-004,Release discipline breaks under cleanup churn,Dev 5,High,Medium,Use release/runbook/control-center artifacts only,,Open,
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\05_Approval_Gates.md") -Content @"
# Approval Gates

## Status levels
- Draft
- Stable Draft
- Approved Working Authority
- Pending Revision

## Gate owners
- Canon approval: TC
- Build-order approval: TC
- Release/runbook approval: Dev 5 + TC
- Inventory final decision: TC

## Rule
Nothing is treated as final because it exists.
It is final only when the proper gate marks it approved.
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\06_Communication_Rules.md") -Content @"
# Communication Rules

## Daily updates
- use one daily update channel/document
- blockers escalate immediately
- decisions are logged in the binder, not lost in chat

## Interrupt rules
- interrupt TC for scope, canon, or release-go/no-go decisions
- do not interrupt TC for normal implementation details already governed by canon

## Rule
Chat is not the system of record.
The binder is.
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\07_Weekly_Review_Packet.md") -Content @"
# Weekly Review Packet

## Include
- week summary
- decisions made
- blockers still open
- risks added
- outputs completed
- binder sections advanced
- next week priorities
"@

Write-Utf8File -Path (Join-Path $binderRoot "03_Operations_and_Delivery\08_Git_GitHub_Azure_Rules.md") -Content @"
# Git / GitHub / Azure Rules

## Current rule
Do not let GitHub or Azure drive the reset.
Inventory and canon come first.

## Git
- always on
- version history preserved
- local truth must remain recoverable

## GitHub
- use for collaboration and protected-main discipline once structure is coherent
- do not let PR churn define architecture

## Azure
- not step 1
- not for thinking
- use when shared staging/demo/pilot is justified
"@

# --------------------------------------------------
# 4. INVENTORY AND KEEP-REWRITE-DROP
# --------------------------------------------------
$inventoryHeader = @"
ItemID,Item,Lane,Category,Owner,CurrentState,CoreModuleAddon,KeepRewriteDrop,FinalDecision,Priority,Notes
"@

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\01_Master_Inventory.csv") -Content ($inventoryHeader + @"
I-001,Crown Core Canon,Canons,Document,Dev 1,Draft,Core,, ,P0,
I-002,SIS Canon,Canons,Document,Dev 2,Draft,Core,, ,P0,
I-003,Admissions Module,Modules,Module,Dev 3,Planned,Module,, ,P0,
I-004,Frontend Shell Canon,Canons,Document,Dev 4,Draft,Core,, ,P0,
I-005,Release Runbook,Runbooks,Runbook,Dev 5,Draft,Core,, ,P0,
"@)

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\02_Core_Inventory.csv") -Content ($inventoryHeader + @"
C-001,Auth,RBAC,Core,Dev 1,Inventory Needed,Core,, ,P0,
C-002,Tenant Isolation,Platform,Core,Dev 1,Inventory Needed,Core,, ,P0,
C-003,Audit Logging,Platform,Core,Dev 1,Inventory Needed,Core,, ,P0,
C-004,Student Master Record,SIS,Core,Dev 2,Inventory Needed,Core,, ,P0,
C-005,Household and Guardian Model,SIS,Core,Dev 2,Inventory Needed,Core,, ,P0,
C-006,Academic Year and Term,SIS,Core,Dev 2,Inventory Needed,Core,, ,P0,
"@)

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\03_Module_Inventory.csv") -Content ($inventoryHeader + @"
M-001,Admissions,Modules,Module,Dev 3,Inventory Needed,Module,, ,P0,
M-002,Re-enrollment,Modules,Module,Dev 3,Inventory Needed,Module,, ,P0,
M-003,Billing Tuition Payments,Modules,Module,Dev 3,Inventory Needed,Module,, ,P0,
M-004,Communications Portals,Modules,Module,Dev 3,Inventory Needed,Module,, ,P1,
M-005,Transportation,Modules,Module,Dev 3,Inventory Needed,Module,, ,P2,
M-006,Food Service,Modules,Module,Dev 3,Inventory Needed,Module,, ,P2,
"@)

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\04_Addon_Inventory.csv") -Content ($inventoryHeader + @"
A-001,Spiritual Life,Addons,Addon,Dev 3,Inventory Needed,Addon,, ,P3,
A-002,Service Outreach,Addons,Addon,Dev 3,Inventory Needed,Addon,, ,P3,
A-003,PD Hub,Addons,Addon,Dev 3,Inventory Needed,Addon,, ,P3,
A-004,Compass,Addons,Addon,Dev 3,Inventory Needed,Addon,, ,P3,
"@)

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\05_Keep_Rewrite_Drop_Rules.md") -Content @"
# Keep / Rewrite / Drop Rules

## Keep
Use only if it is:
- correct
- clean
- testable
- reusable
- aligned with canons

## Rewrite
Use when:
- concept is right
- implementation is messy, stale, inconsistent, or overbuilt

## Drop
Use when:
- duplicate
- outdated
- abandoned
- demo-only
- scope bloat
- experiment with no future place

## Rule
Nothing gets deleted before inventory is complete.
"@

Write-Utf8File -Path (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\06_Archive_Purge_Readiness_Checklist.md") -Content @"
# Archive / Purge Readiness Checklist

- [ ] full inventory complete
- [ ] master inventory complete
- [ ] canons approved
- [ ] keep/rewrite/drop complete
- [ ] archive package complete
- [ ] restore confidence checked
- [ ] purge authority signed off

## Rule
No checklist, no purge.
"@

# --------------------------------------------------
# 5. RUNBOOKS AND CHECKLISTS
# --------------------------------------------------
Write-Utf8File -Path (Join-Path $binderRoot "05_Runbooks_and_Checklists\01_Reset_Runbook.md") -Content @"
# Reset Runbook

## Sequence
1. inventory
2. canon
3. classify
4. archive
5. purge
6. bootstrap
7. rebuild

## Rule
Do not wipe first and then think.
Think first, archive second, wipe third.
"@

Write-Utf8File -Path (Join-Path $binderRoot "05_Runbooks_and_Checklists\02_Build_Sequence.md") -Content @"
# Build Sequence

## Week 1
- inventory everything
- classify nothing yet unless obvious
- no deletion

## Week 2
- rewrite canons
- classify keep/rewrite/drop
- approve phase-one scope

## Week 3
- produce archive packages
- verify archive completeness
- prepare deletion checklist

## Week 4
- controlled purge
- clean bootstrap
- begin Core build

## Build order
1. Core
2. Admissions
3. Re-enrollment
4. Billing / Payments
5. Communications + Portals
6. Second-wave modules
7. Add-ons
"@

Write-Utf8File -Path (Join-Path $binderRoot "05_Runbooks_and_Checklists\03_Release_Runbook.md") -Content @"
# Release Runbook

## Rule
No release is complete because a page renders.

## Release prerequisites
- Definition of Done passed
- permissions enforced
- tenant rules enforced
- tests passed
- release evidence updated
- control-center / execution-window green

## Release checkpoints
- preflight
- deploy
- migration
- smoke tests
- go/no-go
- hypercare
"@

Write-Utf8File -Path (Join-Path $binderRoot "05_Runbooks_and_Checklists\04_Environment_Bootstrap_Checklist.md") -Content @"
# Environment Bootstrap Checklist

- [ ] clean repo structure approved
- [ ] clean frontend shell approved
- [ ] clean backend core structure approved
- [ ] naming canon approved
- [ ] Git / branch rules approved
- [ ] release runbook approved
- [ ] first Core targets assigned
"@

Write-Utf8File -Path (Join-Path $binderRoot "05_Runbooks_and_Checklists\05_Week_1_Work_Assignments.md") -Content @"
# Week 1 Work Assignments

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
"@

# --------------------------------------------------
# Bootstrap summary artifact
# --------------------------------------------------
$created = Get-ChildItem $binderRoot -Recurse -File | Sort-Object FullName |
    Select-Object @{n="Path";e={$_.FullName.Replace($repoRoot + [IO.Path]::DirectorySeparatorChar,"")}}
$created | Export-Csv (Join-Path $artifactRoot "created_files.csv") -NoTypeInformation -Encoding utf8

Write-Utf8File -Path (Join-Path $artifactRoot "SUMMARY.md") -Content @"
# Crown Master Binder Bootstrap Summary

## Binder root
$binderRoot

## Created
- table of contents
- product taxonomy
- phase-one scope
- module priority order
- core/modules/add-ons canons
- SIS/auth/tenant/API/frontend/do-done canons
- team ownership
- RACI
- sprint scorecard
- risk register
- approval gates
- communication rules
- weekly review packet
- Git/GitHub/Azure rules
- master/core/module/add-on inventories
- keep/rewrite/drop rules
- archive/purge checklist
- reset/build/release/environment/week-1 runbooks

## Next required action
1. Fill the master inventory
2. Fill core/module/add-on inventories
3. Approve canons
4. Start Week 1 assignments
"@

Write-Host ""
Write-Host "DONE"
Write-Host "Binder root: $binderRoot"
Write-Host "Artifact root: $artifactRoot"

if ($OpenFiles) {
    Open-IfExists (Join-Path $binderRoot "00_TABLE_OF_CONTENTS.md")
    Open-IfExists (Join-Path $binderRoot "01_Vision_and_Product\01_Mission_and_Product_Taxonomy.md")
    Open-IfExists (Join-Path $binderRoot "02_Architecture_and_Canons\10_Definition_of_Done_Canon.md")
    Open-IfExists (Join-Path $binderRoot "03_Operations_and_Delivery\01_Team_Ownership.md")
    Open-IfExists (Join-Path $binderRoot "03_Operations_and_Delivery\02_RACI.md")
    Open-IfExists (Join-Path $binderRoot "03_Operations_and_Delivery\03_Sprint_Scorecard.csv")
    Open-IfExists (Join-Path $binderRoot "03_Operations_and_Delivery\04_Risk_Register.csv")
    Open-IfExists (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\01_Master_Inventory.csv")
    Open-IfExists (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\02_Core_Inventory.csv")
    Open-IfExists (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\03_Module_Inventory.csv")
    Open-IfExists (Join-Path $binderRoot "04_Inventory_Keep_Rewrite_Drop\04_Addon_Inventory.csv")
    Open-IfExists (Join-Path $binderRoot "05_Runbooks_and_Checklists\02_Build_Sequence.md")
    Open-IfExists (Join-Path $artifactRoot "SUMMARY.md")
}
