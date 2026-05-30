# CROWN Sandbox Evaluator Loop

Status: Operating design baseline
Owner: CROWN Product / Sales / Implementation
Last updated: 2026-05-28

## Purpose

The sandbox is not only a demo surface. It is a controlled evaluator loop that converts interest into proof, feedback, qualification, pilot readiness, and implementation planning.

## End-to-end loop

```text
Lead / invite
  -> segment selection: school, daycare, camp
  -> guided first run
  -> role-specific proof path
  -> optional self-guided exploration
  -> feedback capture
  -> privacy-safe analytics review
  -> sales / implementation follow-up
  -> reset / revoke access
  -> evidence record
```

## Access states

| State | Description | Allowed user |
| --- | --- | --- |
| Internal QA | Full sandbox matrix and all tracks | CROWN internal team only |
| Guided prospect demo | Sales-led or owner-led walkthrough | Qualified lead or invited stakeholder |
| Self-guided prospect sandbox | Time-limited evaluator access after guided orientation | Qualified evaluator |
| Pilot rehearsal | Controlled pre-pilot verification | Approved pilot stakeholder |
| Archived | Expired or revoked access | No active evaluator access |

## Required intake fields

Before external access, capture:

- Organization name
- Evaluator name
- Evaluator role
- Email
- Segment: school, daycare, camp, mixed
- Estimated enrollment or participant count
- Primary evaluation need
- Intended access mode: guided only or guided + self-guided
- Expiration date
- Internal owner

Do not request real student, child, camper, family, staff, financial, health, safety, or disciplinary data.

## Guided first-run rule

First-time external evaluators should start in guided mode unless the evaluator has already received a live orientation.

Self-guided access is allowed only after the evaluator has seen:

1. Demo-data warning
2. Track context
3. Role context
4. Reset boundary
5. Feedback path

## Invite-token operating rules

Every external self-guided evaluator should receive a unique invite token.

Minimum token fields:

- Token ID
- Organization label
- Track restriction: school, daycare, camp, or mixed
- Allowed roles
- Allowed seed pack(s)
- Guidance default
- Expiration timestamp
- Revoked timestamp
- Created by
- Last used timestamp

The invite token must not encode real student, child, camper, family, staff, financial, health, safety, or disciplinary data.

## Feedback loop

Feedback must be captured at three levels:

1. Step-level: Was this proof step clear?
2. Track-level: Did this demo fit your school/daycare/camp context?
3. Decision-level: What would prevent you from adopting CROWN?

Recommended feedback fields:

- Track
- Guidance mode
- Persona
- School/archetype
- Scenario
- Step
- Rating: clear / unclear / not relevant
- Free-text note with real-data warning
- Permission to follow up

Every free-text feedback box must show:

> Demo data only. Do not enter real student, child, camper, family, staff, financial, health, safety, or disciplinary records.

## Privacy-safe analytics

Allowed event metadata:

- Event name
- Timestamp
- Track
- Guidance mode
- Persona
- Archetype / seed pack
- Scenario
- Step number
- Route
- Anonymous session ID or invite ID

Disallowed event metadata:

- Real names entered into forms
- Real student/child/camper/family/staff details
- Payment identifiers
- Health/safety/discipline details
- Full form payloads
- Session recordings that capture form input

## Sales handoff

After a guided or self-guided session, the owner should review:

- Track selected
- Roles viewed
- Steps completed
- Feedback ratings
- Drop-off point
- Questions submitted
- Requested follow-up

Recommended follow-up categories:

| Signal | Follow-up |
| --- | --- |
| Completed guided path and positive feedback | Schedule implementation-fit discussion |
| High daycare/camp interest | Confirm whether workflows need dedicated module packaging |
| Finance-heavy exploration | Schedule tuition/payment workflow review |
| Admissions-heavy exploration | Schedule enrollment pipeline review |
| Confusion/drop-off | Offer short guided walkthrough |
| Real-data warning triggered | Pause access and review data handling |

## Reset and revoke cadence

| Access type | Reset | Revocation |
| --- | --- | --- |
| Internal QA | On demand or nightly | Not applicable |
| Guided prospect demo | Before each session | After session if not continuing |
| Self-guided prospect sandbox | Nightly plus scenario reset | Expiration-based and manual revocation |
| Pilot rehearsal | Before entry and after exit | At pilot close |

## Evidence record

Every external sandbox session should have an evidence record containing:

- Invite ID or session ID
- Track
- Mode
- Persona(s)
- Seed pack
- Start time
- End time
- Feedback status
- Reset status
- Access status: active, expired, revoked
- Internal owner

## Completion rule

A sandbox session is commercially useful only when it produces one of these outcomes:

1. Buyer understands the CROWN value story.
2. Buyer identifies a specific adoption blocker.
3. Buyer requests a deeper workflow review.
4. CROWN captures actionable feedback.
5. CROWN determines the segment is not a fit.

A session that only lets the user click around without feedback, analytics, or follow-up is incomplete.
