# Production Deploy Failure Map Runbook

## Scope
This runbook covers `deploy-prod.yml` and `deploy-prod-dispatch.yml` failure triage.

## Primary Failure Signatures
1. Azure OIDC federation mismatch (`AADSTS700213`)
- Symptom: Azure Login fails in OIDC mode.
- Current mitigation: workflow prints exact expected OIDC subject and audience.
- Required external fix: federated credential subject must match `repo:tcmegahan/Crown2026:environment:production`.

2. Missing/invalid auth secrets
- Symptom: auth guard exits before Azure login.
- Action: validate required secret presence and GUID formatting.

3. AcrPull role assignment check fails
- Symptom: managed identity cannot pull image.
- Current mitigation: retry loop (3 attempts) before hard fail.

4. Post-deploy integrity/build SHA mismatch
- Symptom: `/api/health/` or `/api/integrity/` verification fails.
- Action: check `BUILD_SHA`, `PROD_DEPLOY_TAG`, app settings apply, and tenant probe headers.

## Fast Operator Flow
1. Check failed step name in workflow summary.
2. If Azure Login OIDC failed, compare logged subject to Azure federated credential subject.
3. If AcrPull guard failed, verify managed identity role assignment on ACR scope.
4. If integrity verification failed, inspect health and integrity payloads and app setting values.
5. Re-run after corrective action and capture run URL in incident notes.
