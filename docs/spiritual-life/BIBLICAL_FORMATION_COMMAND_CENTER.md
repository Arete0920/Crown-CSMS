# Spiritual Life & Biblical Formation Command Center

## Status

This document defines the CROWN implementation scope for the expanded Spiritual Life workspace.

The implementation is intentionally repo-backed and centered in the existing `backend/spiritual_life` app and `frontend/dashboards` dashboard surface.

## Product Purpose

The Spiritual Life & Biblical Formation Command Center is the CROWN workspace for chaplains, spiritual life directors, biblical formation leaders, campus pastors, and directors of discipleship.

It supports the role as a strategic formation leader, pastoral-care owner, church-relations ambassador, student leadership developer, family/staff formation partner, and mission-health reporter.

## Primary Role Responsibilities

- Lead chapel and worship planning.
- Generate, review, approve, publish, and archive grade-level devotions.
- Advise on Portrait of the Graduate outcomes.
- Advise on Biblical worldview priorities.
- Maintain spiritual formation evidence.
- Provide spiritual counseling and pastoral care within appropriate referral boundaries.
- Manage prayer requests, spiritual care cases, and sensitive pastoral follow-up.
- Coordinate student spiritual leadership and leadership events.
- Build church partnerships and pastor relationships.
- Host pastor luncheons, campus tours, and Christian Education Sundays.
- Speak in churches and community ministry organizations.
- Coordinate community ministry partnerships.
- Support Christian college, ministry, missions, and calling pathways.
- Equip families and staff through formation resources and events.
- Report mission health to administration and the board.

## Implemented Backend Surfaces

### Domain model module

`backend/spiritual_life/formation_models.py`

Adds the expanded Spiritual Life/Biblical Formation domain model set:

- `PortraitDomain`
- `BiblicalWorldviewPriority`
- `FormationCampaign`
- `FormationArtifact`
- `DevotionalContent`
- `BiblicalIntegrationRecord`
- `SpiritualDomainRating`
- `SpiritualCareCase`
- `ChurchPartner`
- `PastorContact`
- `ChurchEngagementEvent`
- `ChristianEducationSundayCampaign`
- `CommunityOrganizationPartner`
- `StudentSpiritualLeadershipRole`
- `StudentLeadershipEvent`
- `CallingPathwayEvent`
- `FamilyFormationEvent`
- `StaffFormationEvent`
- `SpeakerVettingRecord`

### Serializer module

`backend/spiritual_life/api/formation_serializers.py`

Provides DRF serializers for the new model set.

### View module

`backend/spiritual_life/api/formation_views.py`

Provides tenant-scoped list/create/detail APIs and a mission-control summary endpoint.

### URL module

`backend/spiritual_life/api/formation_urls.py`

Registered under the existing Spiritual Life API route tree:

`/api/v1/spiritual-life/formation/`

## API Route Map

All routes are tenant-scoped through the existing `X-School-Id` resolver.

| Route | Purpose |
|---|---|
| `/summary/` | Mission-control aggregate summary |
| `/portrait-domains/` | Portrait of the Graduate domains |
| `/worldview-priorities/` | Biblical worldview priorities |
| `/campaigns/` | Formation campaigns |
| `/artifacts/` | Formation evidence artifacts |
| `/devotions/` | Grade-level/staff/family/student devotional content |
| `/biblical-integration/` | Biblical worldview integration records |
| `/domain-ratings/` | Spiritual/portrait domain ratings |
| `/care-cases/` | Spiritual counseling and pastoral-care cases |
| `/church-partners/` | Church partner directory |
| `/pastor-contacts/` | Pastor/youth pastor/ministry contacts |
| `/church-engagements/` | Guest speaking, pastor luncheons, tours, ministry events |
| `/christian-education-sundays/` | Christian Education Sunday campaigns |
| `/community-partners/` | Ministry/community organization partners |
| `/student-leaders/` | Student spiritual leadership roles |
| `/student-leadership-events/` | Student leadership summits/trainings/commissioning |
| `/calling-pathways/` | Christian college/ministry/calling events |
| `/family-formation-events/` | Parent/family discipleship events |
| `/staff-formation-events/` | Staff devotions, retreats, worldview PD |
| `/speaker-vetting/` | Speaker/ministry vetting records |

## Dashboard Concept

The command center should surface these dashboard cards:

1. Today's Formation Rhythm
2. Daily Devotion Publishing
3. Chapel & Worship
4. Spiritual Care Queue
5. Crisis / Grief / Sensitive Follow-Up
6. Biblical Worldview Priorities
7. Portrait of the Graduate Alignment
8. Student Spiritual Leadership
9. Student Leadership Events
10. Church & Pastor Relations
11. Christian Education Sundays
12. Guest Speaking & Ministry Events
13. Pastor Luncheons / Campus Tours
14. Community Ministry Engagement
15. Christian College & Calling Pathways
16. Family Formation
17. Staff Formation
18. Service & Missions
19. Speaker & Ministry Vetting
20. Formation Evidence & Reports

## Automated Drafting Safeguards

Drafting tools may assist with devotions, family prompts, staff notes, chapel follow-up, and reflection questions. No assisted draft may be published without human review.

Required guardrails:

- Scripture reference present.
- Age-appropriate language.
- No private student/family/staff information.
- No clinical mental-health advice.
- No unsupported doctrinal claims.
- Alignment to school statement of faith.
- Alignment to worldview priority and Portrait domain where applicable.
- Reviewer recorded.
- Version history preserved.

## Care and Counseling Boundary

The system must distinguish pastoral/spiritual care from licensed counseling or clinical mental-health treatment.

Pastoral/spiritual care may include prayer, encouragement, Scripture, discipleship, spiritual support, restoration, reconciliation, grief support, and church connection.

Licensed counseling/mental-health treatment includes diagnosis, therapy, treatment planning, clinical records, and professional counseling interventions.

CROWN must support escalation flags:

- Parent notification required.
- Counselor referral required.
- Administrator review required.
- Safety concern.
- Mandated reporting concern.
- Outside referral made.
- Urgent follow-up.
- Sensitive/confidential.
- No next-step owner.
- Overdue follow-up.

## Church and Community Engagement Scope

The role includes external spiritual leadership and ambassador activity:

- Guest speaking in churches.
- Christian Education Sundays.
- Pastor luncheons.
- Pastor campus tours.
- Youth pastor breakfasts.
- Church partner briefings.
- Ministry organization meetings.
- Community nonprofit/civic engagement.
- Christian college info days.
- Missions/gap-year pathway events.
- Student leadership events.
- Family formation events.
- Staff formation events.

## Verification Runbook

From repo root:

```bash
cd backend
python manage.py check
python manage.py makemigrations spiritual_life --dry-run --check
python manage.py migrate --plan
python manage.py test spiritual_life crown_api.tests.test_metrics_permissions_contract
```

Frontend smoke checks:

```bash
cd frontend/dashboards
npm install
npm run lint
npm run test -- --runInBand
npx playwright test tests/ui/spiritual-life-ui-proof.spec.ts
```

## Open Verification Items

The GitHub connector can create/update files but cannot run Django migrations, import checks, or Playwright tests. Owner-side verification is required before release.

Required checks:

1. Confirm `spiritual_life.formation_models` imports cleanly under Django startup.
2. Generate and inspect a canonical Django migration for the new models.
3. Run `python manage.py check`.
4. Run API permission tests.
5. Smoke-test `/api/v1/spiritual-life/formation/summary/` with an authenticated spiritual-life user and `X-School-Id` header.
6. Smoke-test frontend Spiritual Life dashboard after dashboard copy expansion.

## Release Status

This is an implementation foundation and API surface expansion. It is not production-complete until migrations, runtime checks, permission tests, and dashboard integration tests are green.
