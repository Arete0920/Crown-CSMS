# Mutation Authority Inventory

**Date:** 2026-10-07  
**Scope:** DRF API classes that declare authentication-only permission and expose POST, PUT, PATCH, or DELETE methods.

This inventory supports issue #166. Authentication and tenant scope are not treated as mutation authority. Each retained authentication-only declaration below has a separately verified ownership, role/action, route override, probe-only, or demo-only boundary. School-wide Spiritual Life mutations without such a boundary are hardened by PR #176.

## Hardened by PR #176

The following school-wide Spiritual Life mutation surfaces now use
`CrownModulePermission("spiritual_life.view", write_code="spiritual_life.edit")`:

- student spiritual profiles and profile updates;
- spiritual assessments;
- chapel events and chapel attendance;
- small groups, membership, sessions, and session attendance;
- prayer requests and prayer-request updates;
- pastoral-note create/update/delete, in addition to the existing pastoral-role check;
- formation domains, priorities, campaigns, artifacts, devotions, integration records, ratings, care cases, church/community partner records, leadership/calling/family/staff formation records, and speaker vetting.

View-only principals retain read authority and are deterministically denied school-wide writes.

## Retained authentication-only declarations with explicit secondary authority

| Surface | Classification | Enforced authority |
| --- | --- | --- |
| `academics/school_profile_views.py:SchoolProfileView.patch` | role-scoped | superuser or same-school `HEAD_OF_SCHOOL` |
| `academics/views.py:SchoolProfileView.patch` | role-scoped compatibility surface | superuser or same-school `HEAD_OF_SCHOOL` |
| `academics/transcript_issuance_views.py:TranscriptIssuanceCollectionView.post` | role/action scoped | transcript issuance authority; student and school scope |
| `apps/compliance/api/parent_rights.py:ParentDataRightsRequestView.post` | self-service | authenticated requester creates their own data-rights request in tenant context |
| `crown_api/billing_api/drf_views.py:BillingRunCreateApiView.post` | route-scoped finance mutation | canonical URL overrides with `finance.edit` |
| `crown_api/billing_api/views.py:PaymentsCreateView.post` | route-scoped finance mutation | canonical URL overrides with `finance.edit` |
| `crown_api/billing_api/views.py:PaymentsApplyView.post` | route-scoped finance mutation | canonical URL overrides with `finance.edit` |
| `discipline/api/views.py:DisciplineIncidentsListCreate.post` | action-scoped | `student-care.create` |
| `discipline/api/views.py:DisciplineIncidentActions.post` | action-scoped | `student-care.edit` / close authority according to requested action |
| `servicehours/api/views.py:ServiceEntriesListCreate.post` | self-service or role-scoped | authenticated student's own record or `service.manage` scope |
| `servicehours/api/views.py:ServiceApproveReject.post` | action-scoped | `service.approve` |
| `sandbox_demo/views.py:SandboxParentEnrollmentView.post` | demo self-service | open sandbox session, Heritage demo parent/school, accepted application, and terms checks in the service boundary |
| `crown_api/release_gate_views.py:TranscriptGenerateProbeView.post` | probe-only | returns release-certification routing metadata only; explicitly does not issue or persist a transcript |

## Unreachable legacy duplicates

`comms/api/views.py` still contains legacy `ThreadPostMessage`, `ComposeThread`, and
`SendTestEmail` classes. They are intentionally not wired in
`comms/api/urls.py`; the URL module documents the retirement of those incompatible
duplicate write endpoints. Production traffic uses the canonical communications
surfaces instead.

## Public-by-design sandbox mutations

The sandbox event and feedback endpoints use `AllowAny` by design for synthetic
demo telemetry. They are outside the authentication-only set and enforce sandbox
payload restrictions, including prohibited-real-data filtering for feedback.
They must never become production student/family mutation authority.

## Regression control

`tools/verify_mutation_authority.py` compares every pull request or governed push
against its base and rejects newly introduced DRF classes that combine a sole
`IsAuthenticated` permission declaration with POST/PUT/PATCH/DELETE methods.
Repository Policy runs this verifier on every pull request and on relevant backend
pushes. Intentional self-service or role/object-authorized mutations must be
implemented and tested explicitly rather than silently expanding the historical
authentication-only inventory.

This inventory does not treat tenant scoping as authorization and does not waive
object-level or action-level checks. Any retained entry that loses its secondary
authority must be converted to an explicit permission boundary.
