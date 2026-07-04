# Pilot Readiness Action Register

Status: **DRAFT / NOT APPROVED**
Date opened: 2026-07-02

This register lists non-runtime actions needed before a controlled pilot decision. It is not a release approval.

## Action register

| ID | Area | Action | Owner | Status | Evidence location |
|---|---|---|---|---|---|
| PRA-001 | Pilot scope | Select first pilot school and document scope. | Founder/Product Owner | OPEN | TBD |
| PRA-002 | Pilot scope | Define exact pilot modules and out-of-scope modules. | Founder/Product Owner | OPEN | TBD |
| PRA-003 | Pilot scope | Define exact pilot roles and required routes. | Founder/Product Owner / Technical owner | OPEN | TBD |
| PRA-004 | Runtime proof | Complete same-SHA role-path proof after PR #1237 is settled. | Technical owner | OPEN | PR #1237 / issue #1220 |
| PRA-005 | Customer readiness | Finalize customer packet and approval record. | Founder/Product Owner | OPEN | TBD |
| PRA-006 | Agreement readiness | Decide whether pilot uses synthetic-only scope or executed agreement paperwork. | Founder/Product Owner | OPEN | TBD |
| PRA-007 | Continuity rehearsal | Complete and record one continuity rehearsal before pilot. | Technical owner | OPEN | TBD |
| PRA-008 | Incident process | Complete and record one incident-response tabletop before pilot. | Founder/Product Owner / Technical owner | OPEN | TBD |
| PRA-009 | Support process | Activate support intake, access approval, and logging procedure. | Founder/Product Owner | OPEN | TBD |
| PRA-010 | Accessibility | Run and archive current accessibility/responsive proof. | Technical owner | OPEN | TBD |
| PRA-011 | Governance | Refresh PE-001 through PE-015 at the decision SHA. | Founder/Product Owner | OPEN | `pilot-entry-gate-scorecard.md` |
| PRA-012 | Final decision | Founder/Product Owner pilot-entry signoff. | Founder/Product Owner | OPEN | TBD |

## Status legend

| Status | Meaning |
|---|---|
| OPEN | Work not complete. |
| IN_PROGRESS | Work started but not settled. |
| BLOCKED | Cannot proceed until a named dependency clears. |
| READY_FOR_REVIEW | Evidence exists and needs review. |
| CLOSED | Evidence accepted. |

## Current blockers

| Blocker | Impact | Dependency |
|---|---|---|
| Runtime proof not green | Blocks role-path and pilot-entry confidence. | PR #1237 |
| Operational readiness records missing | Blocks PE-010, PE-011, PE-012. | Founder/Product Owner and technical owner actions |
| Customer/legal readiness not settled | Blocks PE-008 and PE-009. | Founder/Product Owner decision |
| Decision SHA not frozen | Blocks final PE refresh. | Runtime and documentation lanes must settle first |

## Rule

Do not mark any item CLOSED without a concrete evidence location.
