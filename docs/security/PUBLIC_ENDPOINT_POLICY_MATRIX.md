# Public Endpoint Policy Matrix

Updated: 2026-10-18
Machine authority: docs/security/public_endpoint_policy_matrix.json

| Path | Symbol | Status | Owner |
|---|---|---|---|
| backend/analytics/api_health.py | public_status | approved | Platform Security |
| backend/applications/views_admissions.py | admissions_public_config | approved | Admissions Platform |
| backend/applications/views_admissions.py | admissions_submit | approved | Admissions Platform |
| backend/board_oversight/api_governance.py | public_roadmap | approved | Governance Platform |
| backend/board_oversight/api_governance.py | release_notes | approved | Governance Platform |
| backend/crown_api/ops_views.py | ensure_ci_user | temporary | Platform Engineering |
| backend/crm_marketing/api/inquiries.py | inquiry_collection (POST only) | approved | Admissions Platform |
| backend/crm_marketing/api/inquiries.py | inquiry_start (POST only) | approved | Admissions Platform |
| backend/onboarding/api_onboarding.py | solomon_articles | approved | Onboarding Team |
| backend/onboarding/api_onboarding.py | solomon_article_detail | approved | Onboarding Team |
| backend/onboarding/api_onboarding.py | solomon_context | approved | Onboarding Team |
| backend/onboarding/api_onboarding.py | solomon_categories | approved | Onboarding Team |
| backend/onboarding/api_onboarding.py | solomon_playbooks | approved | Onboarding Team |
| backend/onboarding/api_onboarding.py | solomon_search | approved | Onboarding Team |
| backend/crown_api/dashboards/views.py | get | approved | Dashboard Platform |

## Admissions inquiry capture and continuation

The inquiry additions approve only `POST /api/v1/crm/inquiries/` and `POST /api/v1/crm/inquiries/<uuid:inquiry_id>/start/`, plus their existing `/api/crm/` aliases. The collection's GET branch requires authentication, the tenant header, and `admissions.view` for that school. Staff updates remain separately authenticated and require `admissions.edit`. The tenant middleware exception is limited to the two POST paths; it grants no general CRM exemption.

Capture resolves one active school by UUID or exact, unambiguous campus name and rejects conflicting school headers. It requires explicit permission to respond, records optional follow-up permission separately, validates bounded contact and attribution input, rejects the honeypot, and rate-limits by school/IP and school/email. Persistent idempotency binds the random request key to the school and submitted payload. Unverified contact matches never return existing family records or another inquiry's capability.

The minimal receipt carries a signed school/inquiry/nonce capability with a 30-day maximum lifetime and a stored expiry. Starting an application requires that capability in the POST body, verifies school, signature, age, nonce, and expiry under a row lock, and records the start once. Invalid or wrong-school capabilities receive the same unavailable response. Public responses use `Cache-Control: no-store` and do not disclose family contact details. Application submission revalidates the capability and reuses its restricted stored receipt so retries do not create another household or another set of child applications.

Implementation proof is in `backend/crm_marketing/tests/test_inquiry_capture.py`: `test_public_school_resolution_is_exact_and_header_cannot_conflict`, `test_invalid_or_unconsented_capture_creates_no_records`, `test_campaign_scope_and_submission_throttles`, `test_retries_are_persistent_and_contact_matches_do_not_grant_access`, `test_capability_start_is_idempotent_and_rejects_other_school_nonce_and_expiry`, `test_inquiry_to_multichild_application_preserves_source_and_real_times`, `test_bad_application_capability_never_falls_back_to_new_household`, and `test_staff_queue_requires_scope_and_records_real_follow_up`. These cases exercise the tenant middleware with `TENANT_HEADER_REQUIRED=True`. The machine entries contain the corresponding proof references.

Run `python tools/verify_public_surface_policy.py` to verify exact inventory coverage. The scanner, approval rules, and CSRF exception inventory are unchanged by this registration.
