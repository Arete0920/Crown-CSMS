# Production Deploy Secret Prerequisites

## Authentication Inputs
- Preferred path:
  - `AZURE_CREDENTIALS` (JSON with `clientId`, `clientSecret`, `tenantId`, `subscriptionId`)
- Fallback OIDC path:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`

## Verification Inputs
- `PROD_BASE_URL`
- `PROBE_TENANT_ID`

## Notification Input
- `SLACK_WEBHOOK_URL` (optional; notification step is conditional)

## Validation Rules Implemented in Workflow
1. Missing required auth inputs fail fast.
2. GUID format validation is enforced for OIDC identifiers.
3. `AZURE_CREDENTIALS` JSON schema keys are validated before login.
4. Post-deploy integrity checks fail on non-ok status or SHA mismatch.

## Operator Note
If OIDC is used and login fails with `AADSTS700213`, update Azure federated credential subject to match workflow-emitted subject exactly.
