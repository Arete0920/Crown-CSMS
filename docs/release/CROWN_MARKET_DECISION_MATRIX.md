# Crown Competitor and Marketplace Decision Matrix

Status: Positioning governance matrix
Updated: 2026-05-28

Legend:
- Match: required parity for buyer trust
- Differentiate: core Crown edge
- Ignore: intentionally out of focus
- Defer: planned but not in current gate
- Standalone Candidate: may be sold separately after proof

| Category | Decision | Rationale | Current Evidence Anchor |
|---|---|---|---|
| Core SIS safety (auth/tenant/RBAC) | Match | Must be non-negotiable table stakes | docs/release/FINAL_RELEASE_GATE.md |
| Admissions and enrollment workflows | Match | Required operational trust layer | docs/release/MODULE_INVENTORY.md |
| Billing and payments | Match | Direct operational and financial risk | docs/release/MODULE_INVENTORY.md |
| Attendance and gradebook operations | Match | Daily-use requirement | docs/release/MODULE_INVENTORY.md |
| Communications and portals | Match | Parent/staff usability baseline | docs/release/MODULE_INVENTORY.md |
| Crown Compass institutional scoring | Differentiate | Strategic leadership product signal | docs/release/crown_compass_closeout/ |
| Board Governance Suite | Differentiate | Executive/board-facing value | docs/release/board_governance_suite_closeout/ |
| Spiritual Life and Service/Outreach | Differentiate | Mission-fit advantage for Christian schools | docs/release/spiritual_life_closeout/ |
| Home Academy / Homeschool Affiliation Module | Standalone Candidate | Enables Christian schools to operate school-branded homeschool, hybrid, course-only, activity, and diploma-track programs while preserving school control over academics, eligibility, billing, capacity, records, and participation rules. | docs/architecture/CROWN_HOME_ACADEMY_CANON.md |
| PD Hub | Defer | Add-on value strong but lower urgency than governance + mission layer | docs/release/pd_hub_closeout/ |
| Extended discipline workflows | Defer | Valuable, but follows core and second-wave stability | docs/release/extended_discipline_workflows_closeout/ |
| Broad adjacent CRM-style expansion | Ignore (current phase) | Scope control and release discipline | docs/release/KNOWN_GAPS_AND_DEFERRED_ITEMS.md |
| Mission Suite add-ons as separate SKU | Standalone Candidate | Conditional on standalone policy proof | docs/release/CROWN_PACKAGING_TIER_CANON.md |
| CompuWerx payment-routing compliance moat | Differentiate | Revenue durability and enforceable economics layer | docs/release/PRIORITY_9_MOAT_PROTECTION_CANON.md |

## Enforcement

Every new roadmap item must be added to this matrix before implementation begins.
If no decision exists here, item is blocked from active build scope.

## Home Academy gate

The Home Academy / Homeschool Affiliation Module may proceed only as a controlled premium add-on. It must not claim diploma-pathway completion until school-of-record status, transcript staging, registrar approval, graduation audit, and diploma issuance workflows are implemented and verified with proof artifacts.
