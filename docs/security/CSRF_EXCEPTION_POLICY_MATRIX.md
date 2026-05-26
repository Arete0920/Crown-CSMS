# CSRF Exception Policy Matrix

Updated: 2026-05-26
Machine authority: docs/security/csrf_exception_policy_matrix.json

| Path | Symbol | Status | Owner |
|---|---|---|---|
| backend/advancement/api.py | stripe_webhook | approved | Advancement Payments |
| backend/crown_api/auth_views.py | login | approved | Identity Platform |
| backend/crown_api/auth_views.py | refresh | approved | Identity Platform |
| backend/crown_api/dev_token_views.py | dev_token | temporary | Platform Engineering |
| backend/crown_api/system_views.py | demo_reset_view | temporary | Platform Engineering |
| backend/crown_api/system_views.py | diagnose_db_tables_view | temporary | Platform Engineering |
| backend/crown_api/system_views.py | fix_schema_drift_view | temporary | Platform Engineering |
| backend/finance_setup/wizard_api.py | wizard_status | approved | Finance Setup |
| backend/finance_setup/wizard_api.py | wizard_configure | approved | Finance Setup |
| backend/finance_setup/wizard_api.py | wizard_lock | approved | Finance Setup |
| backend/finance_setup/wizard_api.py | wizard_snapshot | approved | Finance Setup |
| backend/integrations/views.py | compuwerx_webhook | approved | Integrations |
| backend/msauth/views.py | microsoft_callback | approved | Identity Platform |
| backend/payments/api_views.py | compuwerx_webhook | approved | Payments |
| backend/subscriptions/views.py | list_school_modules | approved | Subscriptions |
| backend/subscriptions/views.py | activate_module | approved | Subscriptions |
| backend/subscriptions/views.py | deactivate_module | approved | Subscriptions |
| backend/subscriptions/views.py | start_trial | approved | Subscriptions |
| backend/crown_api/billing_api/drf_views.py | BillingRunCreateApiView | approved | Billing Platform |
