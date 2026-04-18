# Crown Master Priority Ladder Dashboard

Status: Execution control dashboard
Updated: 2026-04-14
Owner of record: Crown product lead

## Crown Execution Dashboard

| Priority | Workstream | Primary Owner | Window | Entry Gate | Exit Gate | Status |
|---|---|---|---|---|---|---|
| 1 | Core proof and release path | Dev 1 + Dev 5 | Now | Current repo state frozen; core scope locked | Auth, RBAC, tenant isolation, core routes, deploy path, and release proof all green together | Red |
| 2 | First-wave modules | Dev 3 | Next | Priority 1 at least yellow-to-green | Admissions, re-enrollment, billing/payments, communications, and role-based portals all work end to end | Red |
| 3 | Second-wave operational modules | Dev 3 + Dev 4 | After P2 | First-wave modules stable | Scheduling, activities/events, nurse, transportation, food, volunteer, advanced reporting, extended discipline live as bounded modules | Red |
| 4 | First-wave add-ons / differentiators | Product + Dev 3/4/5 | After P3 | Core and modules stable | Compass, Board Governance, Spiritual Life, Service and Outreach, PD Hub integrated cleanly through contracts | Red |
| 5 | Crown Master Binder + canons | TC + all leads | Now | Ownership model confirmed | Vision/Product, Architecture/Canons, Operations, Inventory/Cleanup, Runbooks all approved and in use | Yellow |
| 6 | Master inventory + keep/rewrite/drop | All leads | Now | Binder structure live | Every asset tagged Core/Module/Add-on and Keep/Rewrite/Drop | Yellow |
| 7 | Packaging and tier alignment | TC + product/marketing/finance | After P1/P2 definition is stable | Core/Modules/Add-ons locked | Crown Core, Essentials, Complete, Mission Suite and standalone rules approved | Yellow |
| 8 | Competitor / market decision matrix | TC + marketing/product | Parallel | Product taxonomy locked | Each category marked Match / Differentiate / Ignore / Defer / Standalone candidate | Yellow |
| 9 | Implementation, support, release operations | Dev 5 + ops/support leadership | After P2 | First-wave modules usable | Onboarding, training, support, escalation, release, monitoring, rollback, and runbooks operational | Red |
| 10 | Moat and expansion discipline | TC + GTM leadership | Later | Product, delivery, and packaging credible | Payment-routing discipline, association/channel execution, retention system, and expansion model protected | Red |

This ladder is consistent with the settled model: Crown is organized as Core, Modules, and Add-ons, with those categories controlling ownership, priorities, and deployment strategy.

First-wave module set:
- Admissions
- Re-enrollment
- Billing / Tuition / Payments
- Communications
- Parent Portal
- Teacher Portal
- Administrator Portal

Recommended owner model:
- Dev 1: Core Platform Lead
- Dev 2: SIS Core Lead
- Dev 3: Module Lead
- Dev 4: Frontend / UX Lead
- Dev 5: Integration / QA / Release Lead
- Product lead: final product authority

## What Green Means

| Area | Green means |
|---|---|
| Core proof | Core routes, tenant/role enforcement, deploy/release path, and regression proof all pass together |
| First-wave modules | Inquiry -> enrollment, re-enrollment, payment flows, and role-based views are all usable end to end |
| Binder/canons | The Master Binder is the real source of truth, not chats and memory |
| Inventory | Every major asset has an owner, classification, and decision |
| Packaging | Architecture and commercial packaging match |
| Operations | Crown is implementable, supportable, and release-safe |

Binder governing sections:
- Vision and Product
- Architecture and Canons
- Operations
- Inventory and Cleanup
- Runbooks

## Immediate Next 14 Days

| Day range | Focus | Owner |
|---|---|---|
| Days 1-3 | Finish Priority 1 proof plan and freeze scope | Dev 1 + Dev 5 + TC |
| Days 1-5 | Build master inventory and tag Keep / Rewrite / Drop | All leads |
| Days 3-7 | Finalize Core, Modules, Add-ons, Naming, API, Frontend Shell, and Definition of Done canons | Dev 1/2/4/5 + TC |
| Days 7-14 | Start first-wave module closure in order: Admissions -> Re-enrollment -> Billing/Payments -> Communications/Portals | Dev 3 with Dev 2/4/5 support |

Sequencing rule:
Core first, then Admissions, Re-enrollment, Billing/Payments, Communications/Portals, then second-wave modules, then add-ons.

## Executive Read

Current board-level picture:
- Architecture model: decided
- Ownership model: decided
- Governance structure: partially defined, not yet fully operational
- Core proof path: still the top blocker
- Commercial module path: clear, but not yet complete

Decision rules:
- No new scope outside Priorities 1, 5, and 6 until Priority 1 is green.
- No serious add-on expansion until Priorities 2 and 3 are stable.

## Operating Rule

Prove Core -> finish first-wave modules -> finish second-wave operations -> add differentiators -> lock governance and packaging -> scale delivery -> protect the moat.
