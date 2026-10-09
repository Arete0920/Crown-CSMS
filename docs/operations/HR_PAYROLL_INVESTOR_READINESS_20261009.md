# CROWN HR, hiring and payroll execution boundary
Status: proposed operational plan; no provider contract, employer enrollment or production payroll verified.
Reviewed: 2026-10-09. Source baseline: 4ba450a8c25b1cb1bf6caa5999a486e65b38ea7b.

## Decision
Use a licensed third-party payroll/tax operator for Arete Advisory Group. Build CROWN-specific staff operations and provider-neutral integration. Do **not** build a payroll tax calculation/filing or employee direct-deposit engine in CROWN. Neither payroll-provider selection nor a commercial arrangement is approved by this document. Separate Arete (employer operations) from school-tenant HR (customer software).

## Evidence and approved planning inputs
- Approved October 4 founding base salary plan: six roles totaling $313,000 annually **before** taxes, benefits, bonuses, commissions and other employer burden. This is an annualized proposed budget, not actual paid payroll.
- Founder-stage pay by role: engineering $70k; sales $45k; implementation $48k; operations/finance $45k; training/school success $45k; founder $60k.
- Commission policy: 5% of eligible first-year *collected* new-school revenue, split equally among materially contributing originators/participants, 50% after successful go-live and 50% after 90 days conditional on continued school/collection status. This needs signed plan, definitions, refund rules and payroll review before activation.
- Five proposed founding equity allocations of 2% each are plans until legally issued/vested under executed documents.
- The October 5 supporting model proposes 17 paid FTE at end-2027 and 34 at end-2028; capacity assumptions, hiring triggers, cash-flow exposure and affordability must be reviewed. These projections are not signed employment commitments.
- Do not represent October-December unpaid private-company labor as legally cleared. Obtain counsel's worker classification and wage/hour determination before using that arrangement. Equity does not by itself satisfy wage laws.
- The repository tracks canonical `core.Staff` requirements, while `hr.Employee` is a separate compatibility directory; do not silently equate them. Current HR launch-preview dashboard contains template snapshot hiring/payroll counts, not real payroll evidence.

## Buyer/investor people-operations closing register
Each line requires owner, due date, external/private evidence reference, independent reviewer where relevant, and explicit disposition.
| Area | Deliverable | Current status |
| --- | --- | --- |
| Corporate | Confirm employer entity formation, EIN, legal authority, equity capitalization and governance actions | External verification required |
| Team | Named roster, actual status (employee/contractor/advisor), work location, supervisor, signed offer/start date | Not verified |
| Agreements | Employment/contractor agreements, confidentiality, inventions/IP assignment, restrictive terms counsel-approved | Not verified |
| Equity | Award authorizations, percentages, vesting, dilution, tax/legal review and signed documents | Planned, not verified |
| Payroll | Provider selection, pricing, implementation ownership, bank verification and first-cycle test | Not configured |
| Employment tax | Federal/state registrations, worker state nexus, withholding setup, unemployment contributions, reconciliations | External verification required |
| Employment law | FLSA worker classification, wages/overtime, final pay, paid leave and recordkeeping by worker jurisdiction | Counsel review required |
| Onboarding | Form I-9 and W-4 employer process, state new-hire reports, authorization to work, policies, signed acknowledgments | Workflow to implement |
| Insurance | Workers compensation and other legally/contractually required coverage | Evidence required |
| Security | Least-privilege joiner/mover/leaver, MFA, personnel confidentiality, training evidence and actual revocation tests | Operating evidence required |
| Continuity | Backup decision maker, infrastructure administration deputy, key-person access/custody | Proposed |
| Forecast | Monthly headcount/start-date timing, salary burden, benefit costs, incentive accrual, cash runway and reserves | Reconcile with current buyer model |

Use private, access-controlled storage for actual personnel files. The public GitHub repository must never contain SSNs, birth dates, home addresses, bank credentials, Form I-9 documents, paystubs, actual compensation by named employee, or signed HR agreements.

## Vendor evaluation and implementation acceptance
Shortlist Rippling and Gusto. Request comparable written quotes for six initial workers, expected hiring growth, payroll jurisdictions, taxes/filings, benefits, support, onboarding, offboarding, contractor handling, commissions, 1099/W-2, data export, API/webhooks, SOC assurance and total 24-month cost. Verify minimums, feature tiers, contract termination and integration entitlements. Public marketing prices alone are not binding offers. Procurement recommendation only after evaluation; no vendor agreement executed.

### CROWN implementation roadmap
1. **P0:** Repair explicit staff-onboarding edit authorization, add denial/regression tests, preserve school isolation and normal privileged workflow. Avoid changes to payroll.
2. **P1:** Define canonical staff authority and migration compatibility; separate public demo snapshots from live data; introduce a private personnel-lifecycle record with statuses, role permissions, training requirements and audit events.
3. **P2:** Build provider-neutral outbound payroll-change requests, no direct secrets in the frontend, verified webhook signature, idempotent processing, retry/dead-letter handling and immutable audit evidence. Use a provider's approved scoped integration with consent. Never send a payroll instruction without tenant authorization and explicit administrator approval.
4. **P3:** Reconcile payroll/HR statuses through vendor-confirmed events, support deprovisioning, reporting and commission export. Treat payroll provider as system of record for payroll and tax filings, CROWN for school personnel operations only.
5. **P4:** Demand-driven school rollout after data-protection review, vendor contracts, end-to-end test transactions in provider sandbox and operational signoff.

### Non-negotiable product invariants
- Strict per-school tenant isolation and separate read/write grants; GET requests must not mutate state unless explicitly declared and authorized.
- Employee compensation, performance and discipline records need more restrictive permissions than ordinary staff directory access; parent/student roles receive none.
- No credential, financial account, tax-ID or sensitive employment document stored in public source, fixtures, analytics, logs or model-assistance prompts.
- External provider credentials are server-side secrets; encrypt at rest in approved infrastructure, rotate/revoke and audit.
- Every outbound provider mutation needs approved actor, employee scope, exact request digest, idempotency key, state machine and compensating/error review.
- Do not claim functional payroll integration, compliance certification or signed contracts without test logs and vendor evidence.

## Readiness evidence for investor meeting
Present the approved staffing/compensation baseline, budget assumptions, the documented software scope and this open-item register. Explicitly label planned vs executed. Do not present template payroll KPIs as live, employee equity as issued, startup unpaid labor as legal, or payroll filings as configured.

## Source links
- Approved staffing baseline: https://docs.google.com/document/d/10pgA-ohzIcCGi5r68NU0zR38c6yHkaD_6k4Pi4d3IgA/edit
- Supporting model: https://docs.google.com/spreadsheets/d/1KdTdh2Gj2A89qPGCkNO8_nRxxmEYPx9I/edit
- Current buyer package: https://drive.google.com/file/d/1qGbjHD_8quAItcvv05kP1sskVrXtUKH-/view
- HR canonical requirements: docs/engineering/STAFF_REQUIREMENTS.md
- Current implementation: backend/hr/, backend/staff_onboarding_wizard/, frontend/dashboards/src/config/dashboardTemplates/hrDashboard.js
