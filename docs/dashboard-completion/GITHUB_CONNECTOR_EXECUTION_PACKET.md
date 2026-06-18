# GitHub Connector Execution Packet: Dashboard Completion Program

Date: 2026-06-18
Scope: Repository-side controls, issues, PRs, reviews, and certification governance.

## Connector branch

```text
docs/dashboard-plan-20260618
```

## Files created by connector in this branch

```text
docs/dashboard-completion/DASHBOARD_COMPLETION_PROJECT.md
docs/dashboard-completion/VS_CODE_EXECUTION_PACKET.md
docs/dashboard-completion/GITHUB_CONNECTOR_EXECUTION_PACKET.md
```

## What the connector lane is responsible for

1. Create documentation-control branch.
2. Commit planning/control files.
3. Open a draft PR for the dashboard completion project controls.
4. Create a master tracking issue.
5. Create batch tracking issues.
6. Keep issue language aligned with current evidence: dashboards are MAPPED, not complete.
7. Route independent review to someone other than TC.
8. Preserve docs/CURRENT_RELEASE_STATUS.md as release authority.
9. Avoid product-code changes in the planning/control branch.
10. Do not claim dashboard certification until evidence packets exist.

## Master tracking issue body

```markdown
# Dashboard Completion Program: 40-dashboard live-data and certification closure

## Purpose

Create and execute the dashboard completion program for CROWN.

This is not a redesign effort. Existing dashboard structure, visual format, shell, route/nav philosophy, and widget language remain the baseline. The work is to complete live-data wiring, KPI contracts, provenance, permission proof, tenant proof, runtime proof, and certification.

## Current verified state

- 40 dashboard rows exist.
- 40/40 dashboards are MAPPED.
- 0/40 dashboards are live-data certified.
- Current common blocker: route registered but live-data not wired.
- Existing registry coverage is not completion.
- Sample/template data is not production proof.
- TC cannot self-approve certification.

## Project batches

### Batch 0: Control dashboards

- dashboard-certification-center
- release-reliability
- compliance-audit

### Batch 1: Operational school backbone

- attendance
- billing
- gradebook
- communications
- registrar
- school-administrator

### Batch 2: Commercial and role experience

- admissions
- financial-aid
- parent
- teacher
- student
- activities-athletics

### Batch 3: Operational expansion

- scheduling
- health-office
- transportation
- food-service
- facilities
- safety-security
- hr
- it-support

### Batch 4: Mission, advancement, and enrichment

- chaplain-spiritual-life
- portrait-service
- curriculum-pd
- fine-arts
- library-media
- volunteer-management
- advancement
- advancement-operations
- alumni-relations
- school-board
- network-benchmarking

### Batch 5: Platform operations and specialized dashboards

- master-control
- implementation-success
- data-migration
- integrations-automation
- revenue-operations
- summer-camp
- extended-care
- athletics-director

## Definition of done

A dashboard is complete only when it reaches CERTIFIED.

Required statuses:

- MAPPED
- DATA_CONTRACTED
- API_WIRED
- UI_WIRED
- PERMISSION_PROVEN
- TENANT_PROVEN
- RUNTIME_PROVEN
- CERTIFIED

## Evidence required per dashboard

- data contract
- summary service/API
- payload provenance
- KPI definitions
- alert definitions
- queue/table/list definitions
- drilldown definitions
- sensitivity classification
- freshness SLA
- loading/empty/error/forbidden states
- unauthenticated denial proof
- unauthorized role denial proof
- authorized role allow proof
- direct URL proof
- cross-tenant denial proof
- frontend route/render proof
- Playwright runtime proof
- screenshot/trace artifact
- independent review

## Guardrails

- No new route sprawl.
- No duplicate dashboards.
- No hidden sample data.
- No dashboard may bypass tenant enforcement.
- No dashboard may bypass role/action permission.
- No dashboard may create shadow Core truth.
- No dashboard may be certified by TC alone.
- No product-code change belongs in the planning-control PR.

## Acceptance criteria for closing this master issue

- 40/40 dashboards have owner assigned.
- 40/40 dashboards have independent reviewer assigned.
- 40/40 dashboards have data contracts.
- 40/40 dashboards have summary APIs or certified snapshot services.
- 40/40 dashboards have frontend wiring.
- 40/40 dashboards have permission proof.
- 40/40 dashboards have tenant proof.
- 40/40 dashboards have runtime proof.
- 40/40 dashboards have evidence packets.
- 40/40 dashboards are CERTIFIED or explicitly marked non-production-visible.
```

## Batch issue template

```markdown
# Dashboard Completion Batch <N>: <batch name>

## Scope

Dashboards:

- <dashboard-key>

## Purpose

<batch purpose>

## Required work per dashboard

- [ ] Assign owner
- [ ] Assign independent reviewer
- [ ] Write data contract
- [ ] Define KPIs
- [ ] Define alerts
- [ ] Define queue/table/list
- [ ] Define drilldowns
- [ ] Define sensitivity classification
- [ ] Define freshness SLA
- [ ] Implement summary service/API
- [ ] Implement permission checks
- [ ] Implement tenant checks
- [ ] Implement frontend wiring
- [ ] Implement loading state
- [ ] Implement empty state
- [ ] Implement error state
- [ ] Implement forbidden state
- [ ] Add backend tests
- [ ] Add frontend tests
- [ ] Add Playwright runtime proof
- [ ] Add screenshot/trace evidence
- [ ] Complete independent review
- [ ] Update dashboard matrix

## Exit criteria

- No dashboard remains MAPPED-only.
- Every dashboard has a payload contract.
- Every dashboard has evidence packet path.
- Every dashboard has current proof status.
- No dashboard has hidden sample/fallback data.
```

## Pull request body for planning-control PR

```markdown
# Dashboard Completion Project Controls

## Purpose

Adds the dashboard completion project controls for the 40-dashboard live-data and certification closure program.

This PR does not change product code. It establishes documentation, local VS Code execution instructions, and GitHub connector governance instructions.

## Verified baseline

- Current dashboard matrix lists 40 dashboards.
- All 40 are MAPPED.
- Current blocker is live-data-wiring.
- Existing dashboard structure and style remain the baseline.
- Registry coverage is not completion.
- TC cannot self-approve dashboard certification.

## Files

- docs/dashboard-completion/DASHBOARD_COMPLETION_PROJECT.md
- docs/dashboard-completion/VS_CODE_EXECUTION_PACKET.md
- docs/dashboard-completion/GITHUB_CONNECTOR_EXECUTION_PACKET.md

## Non-claims

This PR does not certify dashboards.
This PR does not prove live-data readiness.
This PR does not approve sandbox, pilot, production, or release GO.
This PR does not override docs/CURRENT_RELEASE_STATUS.md.

## Required review

Independent review required. TC cannot be the sole reviewer/approver for certification-affecting work.
```

## Connector action list

Completed in connector lane:

- [x] Create branch docs/dashboard-plan-20260618
- [x] Add DASHBOARD_COMPLETION_PROJECT.md
- [x] Add VS_CODE_EXECUTION_PACKET.md
- [x] Add GITHUB_CONNECTOR_EXECUTION_PACKET.md

Next connector actions:

- [ ] Open draft PR from docs/dashboard-plan-20260618 to main.
- [ ] Create master tracking issue.
- [ ] Create batch issue 0.
- [ ] Create batch issue 1.
- [ ] Create batch issue 2.
- [ ] Create batch issue 3.
- [ ] Create batch issue 4.
- [ ] Create batch issue 5.

## Review routing rule

Planning-control PR can be reviewed for completeness. Any dashboard certification promotion must be independently reviewed by someone other than TC.
