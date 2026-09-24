# Crown Student Accountability Architecture Decision

Date: 2026-09-24
Status: Proposed
Branch: architecture/student-accountability-foundation

## Decision

Crown will keep **Daily Dismissal / Student Movement** and **Safety / Emergency Management** as separate operational domains and separate user experiences.

They will share a common **Student Accountability Core** for identity references, current student status, custody/guardian authorization references, movement events, and immutable audit history.

This preserves operational clarity while preventing duplicate student-location and release data.

## Existing Crown constraints preserved

1. Canonical student/guardian/household ownership remains unchanged:
   - Household: `households.Household`
   - Guardian: `households.Guardian`
   - Student: `households.Student`
   - Section enrollment: `academics.Enrollment`
2. The accountability layer references canonical records; it does not become a second source of truth for them.
3. Tenant isolation continues through `school_id`.
4. Crown module RBAC remains mandatory.
5. All consequential state changes must create audit events.
6. Existing `safety` remains the safety domain and will be extended rather than replaced.

## Domain boundaries

### A. Student Accountability Core

Purpose: provide a single authoritative operational status for each student without taking ownership away from canonical student/guardian records.

Responsibilities:
- current operational state
- current location or custody context
- expected destination
- responsible staff member or operational queue
- guardian/authorized-pickup reference
- state-transition history
- audit trail
- emergency snapshot support

Not responsible for:
- editing student demographics
- editing guardians
- editing custody documents
- editing enrollment records

### B. Daily Dismissal & Student Movement

Normal-operation workflows:
- carline
- parent pickup
- authorized alternate pickup
- bus loading
- walker release
- aftercare handoff
- athletics/activity handoff
- early dismissal
- temporary parent dismissal changes
- sibling/carpool grouping
- staging queues
- release confirmation

Design objective: rapid, repetitive, low-friction daily use.

### C. Safety & Emergency Management

Exceptional-event workflows:
- incident command
- lockdown
- evacuation
- shelter-in-place
- severe weather
- missing student
- emergency accountability
- emergency reunification
- drills
- after-action records

Design objective: high reliability, strict authority, minimal cognitive load, controlled communications.

### D. Command Center

A permission-scoped supervisory surface that can observe both daily operations and emergency status.

The Command Center is not a separate source of truth. It is an operational projection of underlying domain events.

## State model

Initial normal-operation states:

- EXPECTED_ON_CAMPUS
- ABSENT
- IN_CLASS
- IN_TRANSIT
- OFFICE
- NURSE
- ACTIVITY
- ATHLETICS
- AFTERCARE
- DISMISSAL_QUEUED
- DISMISSAL_STAGING
- BUS_BOARDED
- RELEASED
- KNOWN_OFF_CAMPUS

Emergency overlay states:

- ACCOUNTED_FOR
- NEEDS_ASSISTANCE
- MEDICAL
- LOCATION_UNCONFIRMED
- RELOCATED
- READY_FOR_REUNIFICATION
- REUNIFICATION_IN_PROGRESS
- REUNIFIED

Emergency state is an overlay/context, not a destructive replacement of the last known normal operational state.

## Emergency override rule

When an emergency is activated:

1. Crown freezes an accountability snapshot of the current operational state.
2. Normal dismissal mutation endpoints are suspended except for explicitly authorized emergency-command actions.
3. Safety/Emergency becomes the commanding workflow.
4. Teachers and staff continue reporting student status through the emergency interface.
5. Reunification uses the same canonical guardian/authorization references as normal dismissal but a separate emergency workflow and permission set.
6. When the incident closes, normal operations resume only through an explicit command transition.

## Release model

A student release must record:

- student
- school
- release type
- intended destination
- authorized recipient, if applicable
- verification method
- staff verifier
- timestamp
- device/session
- operational context
- exception reason, if applicable

Normal dismissal and emergency reunification may share verification primitives but must not share the same workflow endpoint or permission code.

## Proposed service boundaries

Suggested backend domains:

- `accountability` — shared operational state/event service
- `dismissal` — daily dismissal and handoff workflows
- `safety` — existing safety domain, extended for emergency command and reunification
- `transportation` — remains owner of route/bus operational details
- `households` — remains canonical owner of student/guardian/household
- `academics` — remains canonical owner of section enrollment/rosters

## Core proposed entities

### AccountabilityState
Current projected state for one student.

Fields:
- id
- school_id
- student_id
- normal_state
- emergency_state nullable
- location_code nullable
- responsible_user_id nullable
- expected_destination nullable
- source_domain
- source_record_id nullable
- version
- updated_at

Constraint: one current state row per school/student.

### AccountabilityEvent
Append-only transition history.

Fields:
- id
- school_id
- student_id
- event_type
- from_state
- to_state
- location_code
- actor_user_id
- source_domain
- source_record_id
- context JSON
- occurred_at

### DismissalPlan
Daily/default dismissal intent.

### DismissalChange
Parent/admin same-day exception to default dismissal.

### PickupAuthorization
Operational reference to an authorized guardian/person; does not duplicate guardian identity.

### DismissalQueueEntry
Queue/staging/loading state for a specific dismissal session.

### ReleaseRecord
Immutable release evidence.

### EmergencyIncident
Emergency command object distinct from ordinary incident reporting when an emergency command mode is required.

### EmergencyAccountabilityRecord
Per-student emergency status tied to an EmergencyIncident.

### ReunificationRecord
Emergency release/reunification evidence.

## RBAC

Minimum proposed permissions:

Daily:
- `accountability.view`
- `dismissal.view`
- `dismissal.manage`
- `dismissal.release`
- `dismissal.override`

Emergency:
- `safety.emergency.view`
- `safety.emergency.report_status`
- `safety.emergency.command`
- `safety.reunification.verify`
- `safety.reunification.release`
- `safety.emergency.close`

Emergency command and release permissions must not be implied by ordinary `safety.edit`.

## Non-negotiable safeguards

- no silent release overrides
- no hard deletion of release or emergency accountability history
- no duplicate guardian source of truth
- no cross-tenant lookup
- no emergency control exposed to ordinary carline users
- no automatic physical-release decision based solely on geofence, QR, or device proximity
- every manual override requires identity, reason, timestamp, and audit event
- stale/offline device state must be visibly identified
- emergency mode must support reconciliation after connectivity restoration

## Offline-first requirement

Teacher/staff tablets should be able to:

- retain the assigned roster needed for accountability
- record local status changes while offline
- show synchronization state
- reconcile safely when connectivity returns
- prevent double-release through version/conflict checks

Offline operation must never expose broader school records than the user/device needs.

## Initial implementation sequence

### Phase 1 — Architecture and contracts
- lock state taxonomy
- define transition rules
- define RBAC
- define API contracts
- define emergency override behavior
- define audit requirements

### Phase 2 — Accountability Core
- state/event models
- service layer
- tenant/RBAC tests
- concurrency/versioning
- audit integration

### Phase 3 — Dismissal MVP
- default dismissal plan
- same-day parent/admin changes
- carline queue
- staging
- authorized pickup verification
- release record
- parent confirmation
- bus/aftercare handoff adapters

### Phase 4 — Emergency Command
- emergency activation
- accountability snapshot
- teacher status reporting
- incident command dashboard
- emergency communications hooks
- reunification workflow

### Phase 5 — Offline/tablet hardening
- offline roster cache
- local event queue
- conflict resolution
- device health/status
- drill simulation

## Acceptance gates

Before production, Crown must prove:

1. No student can have two contradictory current accountability states without a surfaced conflict.
2. A normal dismissal release cannot bypass authorization/audit requirements.
3. Emergency mode prevents unauthorized continuation of ordinary dismissal.
4. Command Center totals reconcile to individual student records.
5. Reunification records identify verifier, recipient, student, time, and verification method.
6. Tenant isolation is proven by automated tests.
7. RBAC is proven for teacher, dismissal staff, office staff, administrator, incident commander, and reunification staff.
8. Offline reconciliation is deterministic and audited.
9. Every state transition can be reconstructed from event history.
10. Existing canonical household/student/guardian ownership is not violated.

## Architectural rationale

The school experiences dismissal and emergencies as different operational contexts. Combining their interfaces would increase cognitive load, permissions risk, and accidental-action risk.

However, both contexts need the same underlying answer to a core question:

**Where is this student, who currently has responsibility for the student, and what was the last verified transition?**

Therefore Crown will separate workflows while sharing the accountability substrate.
