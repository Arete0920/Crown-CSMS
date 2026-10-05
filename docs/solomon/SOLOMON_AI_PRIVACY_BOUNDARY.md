# Solomon optional AI and guidance boundary

Owner: TC Megahan. Status: curated guidance and optional OpenAI adapter implemented; external AI disabled.

## Accepted product boundary

Solomon provides optional adult-facing explanations, implementation guidance and
operating resources. Core CROWN must function without generative AI. Teachers,
leadership and spiritual discernment remain human responsibilities. Solomon does
not make admissions, grading, disciplinary, financial aid, health, safeguarding,
pastoral or other consequential decisions. School-specific strategy belongs with
school leadership and Arete Advisory Group.

## Implemented scope

`POST /api/solomon/guidance/` requires authentication, canonical tenant resolution,
and an explicit school-scoped staff role. Platform staff/superuser status alone
is insufficient. Student-role accounts are rejected in the selected school.
School administrators remain responsible for correctly assigning adult staff
roles; this is role-based restriction, not independent age verification.
Both `CROWN_SOLOMON_API_ENABLED` and `CROWN_SOLOMON_GUIDANCE_ENABLED` default false.
Existing Solomon resource and context APIs keep their current behavior.

The JSON request must contain exactly:

```json
{"topic": "onboarding", "human_review_acknowledged": true}
```

Supported topics: `onboarding`, `interpretation`, `governance`, `strategy`, plus
the nine maintained resources in [the approved assistance catalog](SOLOMON_APPROVED_ASSISTANCE.md).
Additional output contains plain-text checklists, reusable drafts, source references,
and a catalog version; the digest covers the full resource.
The response is explicitly labeled curated guidance, not AI-generated. Strategy
returns a human advisory handoff. Acknowledgement means the user accepted the
review requirement; it is not proof that review or a decision has occurred.
The curated endpoint has no decision actions, model calls, or domain-record reads.

The privacy gateway `build_external_payload` constructs only repository-owned
generic guidance. It rejects unknown fields, raw text, uploads, identifiers,
student/parent records, credentials, health, financial, discipline and pastoral
information. It also rejects aggregates until disclosure controls are validated.
It does not ingest existing knowledge-base text: publication or global visibility
alone is not evidence of privacy clearance or permission to send to a provider.
The gateway builds a payload only. The separately gated OpenAI adapter accepts this closed vocabulary and maintained generic checklist/template content; see the [provider release review](SOLOMON_PROVIDER_RELEASE_REVIEW.md).

Successful guidance is durably audited using the existing audit store: internal
actor, school, topic, policy version and source digest. No raw input or generated
output is stored. Audit failure closes the guidance response. Source digest
identifies the catalog version; it does not prove legal or independent approval.
Existing audit retention/access rules apply; review them before production enablement.
Responses use `Cache-Control: no-store`; requests are throttled at 30/minute/user.
Infrastructure request-body/query logging and error telemetry require separate
runtime verification. Rejection cannot undo data a caller improperly submits.

## External activation requirements

External AI remains disabled by default. The optional adapter, tests and separate
release controls are implemented; production activation requires verified private
evidence. Changing the curated guidance flag alone cannot activate it.
The [provider release review](SOLOMON_PROVIDER_RELEASE_REVIEW.md) records current
terms, remaining account checks and exact configuration. Before production use:

- Selected, replaceable provider adapter and contracted data-processing terms:
  no training, advertising or secondary use; documented retention/deletion,
  subprocessors, geographic processing, security and incident notification.
- Qualified legal review of school type, funding, users, jurisdiction and
  contractual duties; applicable consent/notice, COPPA and state requirements.
- Privacy/security impact assessment and approved, rights-cleared grounding
  corpus. No scraped/licensed publisher content without applicable rights.
- Enforced outbound allowlist, no tools or operational writes, timeout/rate/cost
  limits, safe output display, source references and untrusted-output controls.
- Negative privacy, tenant, injection and failure tests; exact-head CI and
  environment-specific evidence; human release authority; kill switch/rollback.
- Any aggregate-data expansion separately proves small-cohort suppression,
  complementary/repeated-query controls and re-identification assessment.
  A numeric cohort threshold alone is not a legal de-identification guarantee.

## Primary legal anchors and limits

Reviewed October 4, 2026. These are design anchors, not an all-state legal opinion.
Applicability and contracts must be reviewed for each deployment; private
Christian schools must not be assumed uniformly covered or exempt.

| Authority | Design implication |
| --- | --- |
| [FERPA, 34 CFR Part 99](https://studentprivacy.ed.gov/ferpa), especially 99.1 and 99.31(b) | Coverage depends on funding/institution. De-identification considers multiple releases and reasonably available information; removing names is insufficient. This slice sends no education records. |
| [Amended COPPA rule](https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule) | Determine child-directed/actual-knowledge applicability to the overall service. Adult-role restriction on this feature does not resolve CROWN-wide child privacy obligations. |
| [HHS/ED FERPA–HIPAA guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/ferpa-hipaa/index.html) | Determine the record holder and coverage; do not assert that all school health information is HIPAA-covered or exempt. This slice prohibits health data. |
| [Delaware Title 14, Chapter 81A](https://delcode.delaware.gov/title14/c081a/index.html) | Review operator/service scope, security, contracted service-provider restrictions and deletion duties. |
| [Maryland Education 4-131](https://mgaleg.maryland.gov/mgawebsite/Laws/StatuteText?article=ged&section=4-131) | Covered information includes indirectly linkable student information. Review statutory scope rather than assuming every private school is covered. |
| [Virginia 22.1-289.01](https://law.lis.virginia.gov/vacode/title22.1/chapter14/section22.1-289.01/) | Review local-school-division contract scope and notice, use and deletion obligations; do not automatically apply public-school provisions to private schools. |

Pennsylvania, New Jersey, other deployment jurisdictions, general consumer privacy,
security/breach obligations, accessibility, discrimination and contract overlays
remain part of the external release review. Pending bills are not enacted law.
No national compliance, legal clearance, provider readiness or deployed-runtime
claim is authorized by this document or passing tests.

## Verification and rollback

Run `pytest backend/solomon/tests backend/onboarding/tests/test_solomon_services.py`
and `python backend/manage.py check` with the supported environment.
Synthetic tests cover provider boundaries as well as rejected data, missing/conflicting tenant, role escalation,
student/parent access, missing acknowledgement, audit failure and no network use for curated guidance.
Revert this coherent change or set `CROWN_SOLOMON_GUIDANCE_ENABLED=false`.
No domain schema migration or payment change is included.
