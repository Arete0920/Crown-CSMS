# Microsoft Entra API Audience Configuration

## Required settings

CROWN Entra bearer authentication fails closed unless both settings are present:

- `AAD_TENANT_ID`: the Microsoft Entra tenant identifier that issues accepted tokens.
- `AAD_API_AUDIENCE`: the exact audience assigned to the CROWN API application registration, normally `api://<api-application-client-id>` or the configured Application ID URI.

Do not configure a blank value, whitespace, the frontend application's client ID, or a Microsoft Graph audience as `AAD_API_AUDIENCE`.

## Deployment procedure

1. Confirm the CROWN API application registration and its Application ID URI in Microsoft Entra.
2. Set `AAD_TENANT_ID` and `AAD_API_AUDIENCE` in protected deployment settings.
3. Restart or redeploy the API so Django reloads the settings.
4. Obtain an access token specifically for the CROWN API scope.
5. Verify that a token with the configured audience and issuer succeeds.
6. Verify that tokens for Microsoft Graph, the frontend application, another API, another issuer, or a missing `aud` claim are rejected.
7. Record the deployment SHA and verification evidence in the controlling release record.

## Audience change or rotation

Treat an Application ID URI or API application change as a controlled authentication migration:

1. Record the current tenant, API registration, and audience.
2. Configure the replacement API audience and update authorized callers to request its scope.
3. Validate the replacement tokens in a nonproduction environment.
4. Update `AAD_API_AUDIENCE`, redeploy, and repeat positive and negative token tests.
5. Promote the same configuration only after retaining nonproduction proof.
6. Remove obsolete scopes or registrations only after every authorized caller has migrated.

CROWN accepts one configured audience. A transition requiring multiple audiences must be implemented and reviewed explicitly rather than weakening audience validation.

## Failure behavior

Missing tenant or audience configuration prevents bearer-token validation before JWKS retrieval. Once configured, signature, expiration, issuer, and audience validation remain enabled. This configuration does not itself authorize production; release authority still requires the current exact-SHA certification process.
