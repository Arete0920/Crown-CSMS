# Crown Packaging and Tier Canon

Status: Commercial packaging policy
Updated: 2026-04-14

## Packaging Model

### Tier 1: Crown Core

Scope:
- Identity/RBAC/tenant isolation
- Student-household truth
- Audit and baseline governance

Use case:
- Minimum safe school operations backbone

### Tier 2: Crown Essentials

Scope:
- Admissions
- Re-enrollment
- Billing/Payments
- Communications + Parent/Teacher/Admin portals

Use case:
- Day-to-day operational MVP for school adoption

### Tier 3: Crown Complete

Scope:
- Attendance
- Gradebook/Scheduling/Sections/Rosters
- Broader school operations (transportation/activities where implemented)

Use case:
- Full daily-use operational platform

### Tier 4: Crown Mission Suite (Add-ons)

Scope:
- Crown Compass
- Board Governance Suite
- Spiritual Life
- Service and Outreach
- PD Hub

Use case:
- Mission and differentiation layer on top of stable operations

## Standalone Add-on Policy

An add-on is standalone-capable only if all are true:

1. It has independent auth and tenant-safe routes.
2. It has documented API contract and role matrix.
3. It has proof tests and runbook coverage.
4. It has packaging and support ownership.

If any are false, add-on remains integrated-only.

## Claim Language Policy

Allowed:
- "Core verified"
- "First-wave operationally proven"
- "Credible operating MVP"

Not allowed without full evidence:
- "Institution-wide production ready"
- "Complete parity across all workflows"

## Pricing Alignment Rule

Pricing pages and proposals must map exactly to:
- Core
- Essentials
- Complete
- Mission Suite

No custom bundle naming that breaks this canon.

## Expansion Annex (Priority #6)

6A standalone-capable expansion first:
- Crown Compass
- Board Governance Suite
- PD Hub
- CRM / Marketing
- Survey / Sentiment
- Mobile App / Family App
- Standalone Schedule Builder

6B mission-distinctive integrated expansion second:
- Chaplain / Pastoral Care
- Portrait of the Graduate
- Mission Metrics
- Deeper Spiritual Life layers
- Deeper Service and Outreach layers

6C ecosystem expansion third:
- API-first contracts
- Integration/webhook surfaces
- Configurable workflows
- Versioned compatibility policy

Authoritative references:
- docs/release/PRIORITY_6_SELECTIVE_EXPANSION_CANON.md
- docs/release/STANDALONE_ADDONS_PRODUCT_TRACK.md
