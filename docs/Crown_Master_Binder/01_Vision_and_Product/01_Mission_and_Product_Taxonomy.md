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
