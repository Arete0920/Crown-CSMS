# CROWN Production Release Roadmap - Target 2026-07-01

Status: ACTIVE PRODUCTION-READINESS ROADMAP
Authority: Non-shipping roadmap until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This roadmap defines the required path to a July 1, 2026 marketplace-ready production release. The date is a target, not proof. Production release requires every gate to pass with current candidate-SHA evidence.

## Production release decision states

| Decision | Meaning |
|---|---|
| PRODUCTION GO | Every required release gate passes and every scored area is 95+ |
| PRODUCTION NO-GO | Any required release gate is missing, failing, stale, or below 95 |

## Required production gates

| Gate | Required final result | Current sprint status |
|---|---|---|
| Final candidate SHA freeze | PASS | NOT DONE |
| Backend full/protected proof | PASS | NOT DONE |
| Frontend full proof | PASS | NOT DONE |
| API contract proof | PASS | NOT DONE |
| Navigation/route proof | PASS | NOT DONE |
| Tenant/RBAC/object proof | PASS | NOT DONE |
| Dashboard KPI provenance | PASS | NOT DONE |
| Wizard completion proof | PASS | NOT DONE |
| Golden-path workflows | PASS | NOT DONE |
| Compliance/customer readiness | PASS | NOT DONE |
| Backup/restore proof | PASS | NOT DONE |
| Production support runbook | PASS | NOT DONE |
| Deploy SHA parity | PASS | NOT DONE |
| Protected-spine packet | PASS | NOT DONE |
| Policy-gate packet | PASS | NOT DONE |
| Release authority convergence | PASS | NOT DONE |
| Final scorecard 95+ all rows | PASS | NOT DONE |
| Final signoff | PASS | NOT DONE |

## Required 95+ areas

All must be 95+:

- Overall production-release readiness.
- Architecture integrity.
- Backend/API.
- Frontend/UI.
- Wiring/connectivity.
- Data plumbing/provenance.
- Tenant/RBAC/security.
- Dashboard/module completeness.
- Wizards/workflows.
- Compliance/customer readiness.
- Release evidence/deploy parity.
- Hygiene/noise.

## Workstream order

### Workstream 1 - Evidence baseline

Run and commit the local evidence pack. No other workstream can be scored above current state until this exists.

### Workstream 2 - P0 release blockers

- Deploy SHA parity.
- Protected-spine runtime/policy packet.
- Release authority convergence.
- Operational readiness.

### Workstream 3 - Architecture and security consolidation

- API canonicalization.
- Route guard audit.
- Role permission matrix.
- Tenant/object permission expansion.
- Settings/source hygiene.

### Workstream 4 - Core role journeys

- Admissions to enrollment to billing/payment.
- Parent journey.
- Teacher journey.
- Student journey.
- Admin/head journey.

### Workstream 5 - Module completion

- Core SIS.
- Finance stack.
- Academic stack.
- Communications/CRM.
- LMS/MS365 learning continuity.
- Operations modules.
- Advancement/board/platform operations.

### Workstream 6 - Customer trust and operations

- FERPA/COPPA posture.
- DPA template.
- Data retention.
- Support access.
- Incident response.
- Backup/restore.
- Subprocessor register.
- Sandbox data policy.
- Customer onboarding.
- Production support.

### Workstream 7 - Final authority

- Final release scorecard.
- Final release authority.
- Final signoff.

## Hard production rule

Do not update production release status to GO until every required row is PASS and every scored area is 95+.

## Current decision

PRODUCTION NO-GO until evidence proves otherwise.
