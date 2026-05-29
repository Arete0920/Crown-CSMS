# Operating Company System Blueprint

> Authority Scope Notice (2026-05-29)
>
> This document is an operating-system blueprint and not a controlling repository-level release authority source.
>
> Current controlling release-authority sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Status: Priority #7 execution blueprint
Updated: 2026-04-14

## Objective

Turn Crown from a strong codebase into a deliverable, supportable, and scalable company product.

## Workstream 1: School Implementation Operations

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Onboarding sequence | Phase-by-phase implementation path | Implementation lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Data migration process | Import templates, validation steps, cutover checks | Data operations lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Configuration standards | Core/Modules/Add-ons config baseline | Solutions architect | docs/release/CROWN_MASTER_BINDER.md |
| Training model | Role-based training plan and schedule | Customer success lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Rollout checklist | Pilot launch readiness checklist | Program manager | docs/release/PILOT_INVESTOR_READINESS_PROOF_PACK.md |
| Pilot-to-live checklist | Go-live gates and acceptance signoff | Release owner | docs/release/FINAL_RELEASE_GATE.md |

## Workstream 2: Support and Customer Success

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Triage model | Intake and classification flow | Support lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Severity model | Sev levels and SLA matrix | Support lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Escalation path | Support-to-engineering escalation map | Engineering manager | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Communications cadence | Update frequency by severity and audience | Customer success lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Knowledge base | Article ownership and review cadence | Support operations | docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md |
| Customer health tracking | Health scoring and risk intervention process | Customer success operations | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |

## Workstream 3: Integration and Ecosystem Operations

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| API contract stability | Version and deprecation policy | Platform engineering | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Import/export standards | Data boundary specs and validation | Integration lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Connector runbooks | Install, auth, retry, and failure guides | Integration operations | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Partner model | Connector ownership and support model | Partnerships lead | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Event/webhook patterns | Delivery guarantee and replay handling | Platform engineering | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Boundary discipline | Core/Modules/Add-ons contract matrix | Architecture owner | docs/release/CROWN_MASTER_BINDER.md |

## Workstream 4: Release and Environment Operations

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Release structure | Canonical release artifact map | Release manager | docs/release/FINAL_INVESTOR_EVIDENCE_INDEX.md |
| Environment promotion | Dev/staging/prod promotion gates | DevOps owner | docs/release/RELEASE_ENV_MATRIX.md |
| Monitoring and alerts | Alert matrix with runbook links | SRE/operations lead | docs/ops/ALERT_RUNBOOK.md |
| Deploy checklist | Preflight/deploy/postflight sequence | Release manager | docs/LOCKDOWN_RUNBOOK.md |
| Rollback/incident | Recovery and incident ownership matrix | Incident commander | docs/LOCKDOWN_RUNBOOK.md |
| Secrets/config | Allowlist-based config discipline | Security owner | docs/ops/ROTATE_SECRETS.md |

## Workstream 5: Compliance and Trust Operations

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Auditability | Decision and change traceability standards | Compliance owner | docs/release/PRIORITY_7_OPERATING_COMPANY_CANON.md |
| Role/tenant proof packs | Repeatable tenant and role evidence bundle | QA/release owner | docs/TENANT_AUDIT_CERTIFICATION.md |
| Privacy/compliance docs | Maintained compliance package | Compliance owner | docs/COMPLIANCE.md |
| Security review rhythm | Scheduled security review process | Security owner | docs/release/SECURITY_GATES_EVIDENCE.md |
| Customer trust materials | Customer-facing confidence packet | GTM + customer success | docs/release/PILOT_INVESTOR_READINESS_PROOF_PACK.md |


## Workstream 6: Partnership-Led Market Capture

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Association channel strategy | Network-first partner model and target cohorts | Platform lead (TC) | docs/release/PRIORITY_8_PARTNERSHIP_MARKET_CAPTURE_CANON.md |
| Referral and case-study flywheel | Reference and referral operating loop | Marketing director | docs/release/PARTNERSHIP_CHANNEL_EXECUTION_PLAYBOOK.md |
| Partner ecosystem expansion | Association and consortium expansion playbook | Platform lead (TC) | docs/release/PARTNERSHIP_CHANNEL_EXECUTION_PLAYBOOK.md |
| Segment expansion gates | Secular/daycare expansion stage gates | Marketing director | docs/release/PRIORITY_8_PARTNERSHIP_MARKET_CAPTURE_CANON.md |
| Channel delivery quality | Partner cohort onboarding quality controls | Client success manager | docs/release/OPERATING_COMPANY_SYSTEM_BLUEPRINT.md |

## Workstream 7: Moat Protection and Value Compounding

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Dual-moat defense | Mission-plus-payment moat protection controls | Platform lead (TC) | docs/release/PRIORITY_9_MOAT_PROTECTION_CANON.md |
| Payment-routing enforcement | Contract, monitoring, and escalation controls | Platform lead (TC) | docs/release/MOAT_COMPOUNDING_EXECUTION_PLAYBOOK.md |
| Success-as-moat execution | Onboarding and retention-quality control loop | Client success manager | docs/canon/CROWN_SOLOMON_CANON.md |
| Continuity and capital discipline | Team continuity and strategic allocation governance | Platform lead (TC) | docs/release/PRIORITY_9_MOAT_PROTECTION_CANON.md |
| Enterprise-value metrics | Durable retention and moat KPI reporting cadence | Finance lead | docs/release/MOAT_COMPOUNDING_EXECUTION_PLAYBOOK.md |

## Workstream 8: Strategic Optionality and Transaction Readiness

| Capability | Required Output | Owner | Evidence Artifact |
|---|---|---|---|
| Transaction-structure flexibility | Recap/raise/M&A optionality framework | Platform lead (TC) | docs/release/PRIORITY_10_OPTIONALITY_FINANCEABILITY_CANON.md |
| Diligence packet operations | Always-ready branch, module, demo, payment, and pipeline evidence set | Release owner | docs/release/STRATEGIC_OPTIONALITY_DILIGENCE_PLAYBOOK.md |
| Valuation proof metrics | Pilot, ARR, implementation, and stability scorecards | Finance lead | docs/release/STRATEGIC_OPTIONALITY_DILIGENCE_PLAYBOOK.md |
| Investor language discipline | Evidence-aligned narrative and disclosure controls | Platform lead (TC) | docs/release/PRIORITY_10_OPTIONALITY_FINANCEABILITY_CANON.md |
| Optionality protection gate | No-urgency decision framework across transaction paths | Platform lead (TC) | docs/release/STRATEGIC_OPTIONALITY_DILIGENCE_PLAYBOOK.md |
## Exit Rule for Priority #7

Priority #7 is complete only when each workstream has:

1. Named owner
2. Current operating artifact
3. Evidence path in release index
4. Review cadence defined
