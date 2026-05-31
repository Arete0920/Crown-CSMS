# CROWN Controlled Pilot Entry / Exit Checklist — 2026-05-29

## Status

**CHECKLIST DOCUMENTED — PILOT NOT APPROVED.**

This checklist defines the exact evidence required before CROWN can enter or exit a controlled pilot. It does not grant pilot approval.

## Pilot entry decision

Pilot entry is **NO-GO** until every P0 item below is green.

### P0 entry gates

| Gate | Requirement | Evidence required | Status |
|---|---|---|---|
| PE-001 | Release authority truth lock | Public status and release docs do not claim GA or pilot approval until signed | NOT_GREEN |
| PE-002 | Full-completion truth gate | `106_crown_full_completion_truth_gate.ps1` passes without `-AllowPreviewData` | NOT_GREEN |
| PE-003 | Dashboard completion gate | `105_dashboard_module_completion_gate.ps1 -Deep` passes with all required env flags | NOT_GREEN |
| PE-004 | Tenant isolation | Cross-tenant data access tests pass for API, UI, object-level access, and exports | NOT_GREEN |
| PE-005 | RBAC | Role matrix and route/API permissions pass for every pilot role | NOT_GREEN |
| PE-006 | Core SIS workflows | Student records, households, enrollment, attendance, scheduling, gradebook, registrar, billing, aid, communications pass end-to-end | NOT_GREEN |
| PE-007 | Wizard workflows | All scoped setup/onboarding wizards complete end-to-end | NOT_GREEN |
| PE-008 | Compliance packet | Compliance/customer-readiness packet legally/product-owner approved | NOT_GREEN |
| PE-009 | DPA/order form | Pilot customer agreement/DPA executed or pilot data limited to sandbox-only non-production data | NOT_GREEN |
| PE-010 | Backup/restore | Restore test completed and documented | NOT_GREEN |
| PE-011 | Incident response | Incident contacts, severity rules, notification workflow, and tabletop/test completed | NOT_GREEN |
| PE-012 | Support access | Support-access approval and logging process active | NOT_GREEN |
| PE-013 | Sandbox/no-real-data | If sandbox pilot, all data synthetic/approved and labeled | NOT_GREEN |
| PE-014 | Accessibility/responsive | Critical flows pass a11y and responsive checks | NOT_GREEN |
| PE-015 | Founder/Product Owner signoff | Pilot entry signoff executed | NOT_GREEN |

## Pilot scope form

- Pilot school/customer: `[TBD]`
- Pilot environment: `[sandbox / production-limited / other]`
- Pilot modules in scope: `[TBD]`
- Pilot users/roles in scope: `[TBD]`
- Data categories in scope: `[TBD]`
- Start date: `[TBD]`
- Exit review date: `[TBD]`
- Rollback plan location: `[TBD]`
- Support contact: `[TBD]`
- Incident contact: `[TBD]`

## Pilot success criteria

Pilot success requires:

1. All scoped users can complete assigned workflows.
2. No critical/high security issue remains open.
3. No cross-tenant, privacy, or RBAC blocker occurs unresolved.
4. Data accuracy/reconciliation is accepted by the school.
5. Support response and escalation are functioning.
6. Backup/restore and rollback remain viable.
7. Accessibility/responsive blockers are closed or formally accepted.
8. Customer and Founder/Product Owner approve exit.

## Pilot exit decision

Pilot exit to GA is **NO-GO** until every P0 exit item below is green.

### P0 exit gates

| Gate | Requirement | Evidence required | Status |
|---|---|---|---|
| PX-001 | Pilot completion | Pilot success criteria signed | NOT_GREEN |
| PX-002 | Security review | No unresolved critical/high security or tenant-isolation issue | NOT_GREEN |
| PX-003 | Privacy/compliance review | No unresolved compliance/customer-readiness blocker | NOT_GREEN |
| PX-004 | Runtime reliability | Uptime/error/support metrics reviewed and accepted | NOT_GREEN |
| PX-005 | Workflow acceptance | All scoped workflows accepted by customer/product owner | NOT_GREEN |
| PX-006 | Data reconciliation | Imported/generated operational data reconciled | NOT_GREEN |
| PX-007 | Support review | Support issues triaged and closure plan accepted | NOT_GREEN |
| PX-008 | Release evidence bundle | Backend/frontend/security/deploy/a11y/responsive evidence current | NOT_GREEN |
| PX-009 | Final authority | Founder/Product Owner GA release signoff executed | NOT_GREEN |

## Signoff blocks

### Pilot entry approval

I approve controlled pilot entry for the scope listed above.

Founder/Product Owner: ____________________________

Date: ____________________________

Customer representative, if applicable: ____________________________

Date: ____________________________

### Pilot exit / GA approval

I approve pilot exit and GA consideration based on attached evidence.

Founder/Product Owner: ____________________________

Date: ____________________________

Customer representative, if applicable: ____________________________

Date: ____________________________
