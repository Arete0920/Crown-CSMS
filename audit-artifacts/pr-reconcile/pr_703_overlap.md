# PR #703 OVERLAP

- Title: Fix backend-gate: create missing Django apps/modules, fix student_records URL prefix, fix related-article exclusion bug, add portrait/services.py, add Solomon regression tests, split article serializers, add visibility gating and audience filtering
- Branch: copilot/fix-student-records-url-routing
- Base: fix/frontend-audit
- Draft: True
- Updated: 2026-04-12T01:36:34Z
- URL: https://github.com/tcmegahan/Crown2026/pull/703
- PR files scanned: 17
- Local overlap count: 17
- High-risk overlap count: 3
- Risk: CRITICAL

## Overlapping Files

- [normal] backend/crown_api/api_v1_urls.py
- [normal] backend/governance/__init__.py
- [HIGH-RISK] backend/governance/urls.py
- [HIGH-RISK] backend/governance/views.py
- [normal] backend/onboarding/solomon_seed.py
- [normal] backend/onboarding/solomon_services.py
- [normal] backend/onboarding/tests/test_solomon_services.py
- [normal] backend/portrait/__init__.py
- [normal] backend/portrait/apps.py
- [normal] backend/portrait/migrations/__init__.py
- [normal] backend/portrait/models.py
- [normal] backend/portrait/services.py
- [normal] backend/student_records/__init__.py
- [normal] backend/student_records/apps.py
- [normal] backend/student_records/migrations/__init__.py
- [normal] backend/student_records/models.py
- [HIGH-RISK] backend/student_records/urls.py