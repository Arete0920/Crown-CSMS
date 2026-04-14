# Crown Master Priority Ladder Dashboard

Status: Execution control dashboard
Updated: 2026-04-14
Owner of record: Crown product lead

## Operating Rule

Prove Core -> finish first-wave modules -> finish second-wave operations -> add differentiators -> lock governance and packaging -> scale delivery -> protect the moat.

## One-Page Execution Dashboard

| Priority | Category | Scope | Primary Owner(s) | Due Window | Status | Gate | Exit Criteria |
|---|---|---|---|---|---|---|---|
| 1 | Core proof and release path | CI governance, route-contract integrity, tenant/role proof, deploy-prod proof | Dev 1 + Dev 5, final sign-off by product lead | Now to 30 days | In progress | Yellow | Single go/no-go proof for auth, RBAC, tenant isolation, student-household truth, admissions-billing dependencies, release-path verification |
| 2 | First-wave modules | Admissions, Re-enrollment, Billing/Tuition/Payments, Communications, Parent Portal, Teacher Portal, Admin Portal | Dev 3 (primary), Dev 2/4/5 support | 30 to 90 days | Planned | Yellow | Inquiry-to-enrollment, re-enrollment, balances/payments, and role-based portal views run end-to-end |
| 3 | Second-wave operational modules | Scheduling, Activities/Athletics/Events, Nurse Office, Transportation, Food Services, Volunteer/Family Engagement, Advanced Board Reporting, Extended Discipline | Dev 3 + Dev 4, contract guard by Dev 1 | 30 to 90 days (after Priority 2 stability) | Planned | Yellow | Daily school operations run on Crown with no shadow records outside Core |
| 4 | First-wave add-ons and differentiators | Spiritual Life, Service and Outreach, Crown Compass, Board Governance Suite, PD Hub | Product-led, then Dev 3/4/5 as assigned | After Priority 1-3 stability | Planned | Yellow | Add-ons integrate via contracts/events and remain standalone-capable where intended |
| 5 | Governance and binder system | Vision/Product, Architecture/Canons, Operations, Inventory/Cleanup, Runbooks as one authoritative binder | Product lead with all lane leads | Now to 30 days (finalize before broader rollout) | In progress | Yellow | Single canonical operating system with no memory-driven decision gaps |
| 6 | Inventory, classification, keep-rewrite-drop | Classify Core/Module/Add-on assets with Keep, Rewrite, Drop tags | All five dev lanes, final approval by product lead | Now to 30 days | In progress | Yellow | Every feature/page/workflow/code asset has explicit classification and disposition |
| 7 | Packaging and pricing alignment | Crown Core, Essentials, Complete, Mission Suite, selective standalone add-ons | Product lead + marketing + finance | After architecture lock, before pilot-scale selling | Planned | Yellow | Packaging map matches architecture boundaries and support model |
| 8 | Competitor and market decision matrix | Match, Differentiate, Ignore, Defer, Standalone candidate decisions by category | Product lead + marketing/product | Before final tier/GTM lock | In progress | Yellow | Every category has explicit strategic decision and evidence anchor |
| 9 | Implementation, support, and operating scale | Onboarding runbooks, training, escalation, release discipline, environment rules, checklists | Dev 5 operationally + implementation/customer success leadership | Expansion layer | Planned | Yellow | Crown is repeatably deliverable and supportable as a platform |
| 10 | Moat and expansion discipline | Faith-native architecture, role-specific UX, payment infrastructure, mission reporting, onboarding quality, network reputation | Product lead + GTM leadership | Expansion layer (after 1-9 stabilization) | Planned | Yellow | Growth compounds into retention and defensibility, not commodity feature churn |

Gate legend:
- Green: exit criteria met and evidence committed
- Yellow: active tranche with open blocking items
- Red: blocked; cannot advance dependent priority

## Owner Map (Canonical)

1. Dev 1: Core Platform Lead
2. Dev 2: SIS Core Lead
3. Dev 3: Module Lead
4. Dev 4: Frontend and UX Lead
5. Dev 5: Integration, QA, and Release Lead
6. Product lead: boundaries, canon approval, build priority, final acceptance

## Timing Map (Canonical)

1. Now through next 30 days: Priorities 1, 5, 6
2. Next 30 to 90 days: Priorities 2, 3
3. After that: Priorities 4, 7, 8
4. Expansion layer: Priorities 9, 10

## Update Cadence

1. Weekly status refresh by lane owners
2. Biweekly gate review by product lead
3. Priority advancement requires explicit gate change and evidence path update
