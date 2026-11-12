# CSRF Exception Policy Matrix

Updated: 2026-11-09
Machine authority: docs/security/csrf_exception_policy_matrix.json

| Path | Symbol | Status | Owner |
|---|---|---|---|
| backend/crown_api/auth_views.py | login | approved | Identity Platform |
| backend/crown_api/auth_views.py | refresh | approved | Identity Platform |
| backend/crown_api/dev_token_views.py | dev_token | temporary | Platform Engineering |
| backend/crown_api/system_views.py | demo_reset_view | temporary | Platform Engineering |
| backend/crown_api/system_views.py | diagnose_db_tables_view | temporary | Platform Engineering |
| backend/crown_api/system_views.py | fix_schema_drift_view | temporary | Platform Engineering |
| backend/integrations/views.py | compuwerx_webhook | approved | Integrations |
| backend/msauth/views.py | microsoft_callback | approved | Identity Platform |
| backend/payments/api_views.py | compuwerx_webhook | approved | Payments |
| backend/subscriptions/views.py | list_school_modules | approved | Subscriptions |
| backend/subscriptions/views.py | activate_module | approved | Subscriptions |
| backend/subscriptions/views.py | deactivate_module | approved | Subscriptions |
| backend/subscriptions/views.py | start_trial | approved | Subscriptions |
| backend/crown_api/billing_api/drf_views.py | BillingRunCreateApiView | approved | Billing Platform |
