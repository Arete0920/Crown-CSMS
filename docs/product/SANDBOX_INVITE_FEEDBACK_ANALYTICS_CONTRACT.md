# CROWN Sandbox Invite, Feedback, and Analytics Contract

Status: Implementation contract
Owner: CROWN Product / Engineering
Last updated: 2026-05-28

## Purpose

This document defines the minimum backend and frontend contract required to support controlled guided and self-guided sandbox evaluation.

## API contracts

### Create invite

```http
POST /api/v1/sandbox/invites/
```

Request:

```json
{
  "organization_label": "Example Christian Academy",
  "track": "school",
  "allowed_roles": ["school_admin", "admissions_director", "finance_director", "teacher", "parent"],
  "allowed_seed_packs": ["heritage_core"],
  "default_guidance": "guided",
  "expires_at": "2026-06-30T23:59:59Z"
}
```

Response:

```json
{
  "invite_id": "sbx_inv_...",
  "url": "https://app.example.test/sandbox?invite=sbx_inv_...",
  "expires_at": "2026-06-30T23:59:59Z"
}
```

### Resolve invite

```http
GET /api/v1/sandbox/invites/{invite_id}/
```

Response:

```json
{
  "invite_id": "sbx_inv_...",
  "organization_label": "Example Christian Academy",
  "track": "school",
  "allowed_roles": ["school_admin", "admissions_director"],
  "allowed_seed_packs": ["heritage_core"],
  "default_guidance": "guided",
  "expires_at": "2026-06-30T23:59:59Z",
  "revoked_at": null
}
```

### Revoke invite

```http
POST /api/v1/sandbox/invites/{invite_id}/revoke/
```

Response:

```json
{
  "invite_id": "sbx_inv_...",
  "revoked_at": "2026-05-28T14:15:00Z"
}
```

### Record event

```http
POST /api/v1/sandbox/events/
```

Allowed request payload:

```json
{
  "event": "sandbox_step_completed",
  "invite_id": "sbx_inv_...",
  "track": "camp",
  "guidance": "guided",
  "persona": "school_admin",
  "school": "cedar-summer-camp",
  "tour": "Session Registration to Daily Roster",
  "step": 2,
  "route": "/school-admin-dashboard"
}
```

Disallowed request payload fields:

- real_name
- student_name
- child_name
- camper_name
- family_name
- phone
- address
- payment_identifier
- health_detail
- safety_detail
- discipline_detail
- full_form_payload

### Submit feedback

```http
POST /api/v1/sandbox/feedback/
```

Request:

```json
{
  "invite_id": "sbx_inv_...",
  "track": "daycare",
  "guidance": "guided",
  "persona": "parent",
  "school": "emmanuel-early-learning",
  "scenario": "Family experience proof path",
  "step": 4,
  "rating": "clear",
  "note": "The daily update path was easy to understand.",
  "follow_up_requested": true
}
```

Validation rules:

- `rating` must be one of: `clear`, `unclear`, `not_relevant`, `blocked`.
- `note` must be optional and length-limited.
- `note` must be scanned for prohibited real-data patterns.
- Feedback forms must show the demo-data warning.

## Minimal data model

### SandboxInvite

Fields:

- id
- organization_label
- track
- allowed_roles
- allowed_seed_packs
- default_guidance
- expires_at
- revoked_at
- created_by
- created_at
- last_used_at

### SandboxEvent

Fields:

- id
- invite_id nullable
- event
- track
- guidance
- persona
- school
- tour
- step nullable
- route nullable
- occurred_at

### SandboxFeedback

Fields:

- id
- invite_id nullable
- track
- guidance
- persona
- school
- scenario
- step nullable
- rating
- note
- follow_up_requested
- created_at

## Security and privacy rules

- Invite IDs must be unguessable.
- Invite tokens must expire.
- Revoked invites must not allow sandbox entry.
- Self-guided external access should require an invite.
- Analytics must not capture form payloads.
- Feedback free text must be warning-labeled and scanned.
- No sandbox record may contain real student, child, camper, family, staff, financial, health, safety, or disciplinary data.

## Acceptance criteria

The invite/feedback/analytics layer is complete only when:

- Invites can be created, resolved, expired, and revoked.
- `/sandbox?invite=...` limits visible track, roles, and seed packs.
- Events are recorded with privacy-safe metadata only.
- Feedback can be submitted from guided and self-guided modes.
- Free-text feedback is scanned for prohibited patterns.
- Admin can review invite activity and feedback.
- Tests prove expired and revoked invites cannot be used.
