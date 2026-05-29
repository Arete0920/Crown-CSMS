# CRM Optional Integration Posture - 2026-05-27

## 1) Current observed behavior
- Admissions submit invokes `_safe_register_crm_submit` from `backend/applications/views_admissions.py`.
- The helper wraps CRM calls in `try/except` and logs failures without aborting admissions persistence.
- Targeted admissions and billing tests pass with CRM service module unavailable in the local environment.

## 2) Whether `crm_marketing.services` exists in current environment
- No `crm_marketing` Python package was found in the current workspace search (`**/crm_marketing/**/*.py`).
- Runtime traces during targeted tests show `ModuleNotFoundError: No module named 'crm_marketing.services'`.

## 3) Whether admissions submit safely degrades when CRM is unavailable
- Yes. `_safe_register_crm_submit` is explicitly fail-safe and logs `crm_marketing_register_submit_failed` instead of failing the request path.
- Observed test runs complete successfully (`26` tests) despite missing CRM module.

## 4) Whether tests explicitly cover fallback behavior
- No dedicated explicit test was found that asserts CRM fallback logging/continuation semantics directly.
- Current evidence is indirect runtime confirmation from passing targeted admissions/billing tests with missing CRM module.

## 5) Current release classification
- **OPTIONAL_SAFE_WITH_RELEASE_NOTE**

Rationale:
- Admissions canonical flow remains functional and test-green without CRM module.
- CRM integration currently behaves as an optional add-on surface, not a hard runtime dependency for admissions submit completion in this environment.

## 6) Required next action
1. Add a focused admissions test that explicitly verifies CRM import failure is caught and admissions submit still succeeds.
2. Add a release note line that CRM marketing hooks are optional/degraded in local packaging unless the CRM add-on is installed.
3. Revisit classification only if product policy requires CRM as a mandatory production dependency.
