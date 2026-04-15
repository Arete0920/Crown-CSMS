# Proof Summary

| Check | Status | Artifact | Notes |
|---|---|---|---|
| DJANGO_CHECK | PASS | artifacts\deep-audit\logs\DJANGO_CHECK.txt | duration_seconds=5.14 |
| SHOW_MIGRATIONS | PASS | artifacts\deep-audit\logs\SHOW_MIGRATIONS.txt | duration_seconds=5.12 |
| OPENAPI_EXPORT | PASS | docs\audit\evidence\openapi.yaml |  |
| CRITICAL_TEST_CLUSTER | PASS | artifacts\deep-audit\logs\CRITICAL_TEST_CLUSTER.txt | duration_seconds=167.76 |
| FULL_BACKEND_REGRESSION | FAIL |  | not run; use -RunFullRegression |
| FRONTEND_LINT | FAIL |  | not run; use -RunFrontendBuild |
| FRONTEND_BUILD | FAIL |  | not run; use -RunFrontendBuild |
| HEALTH_ENDPOINT | FAIL | artifacts\deep-audit\logs\HEALTH_ENDPOINT.txt | health endpoint unavailable |
| INTEGRITY_ENDPOINT | FAIL | artifacts\deep-audit\logs\INTEGRITY_ENDPOINT.txt | integrity endpoint unavailable |
| GH_PR_LIST | PASS | docs\audit\evidence\GH_PR_LIST.json |  |
| GH_RUN_LIST | PASS | docs\audit\evidence\GH_RUN_LIST.json |  |
