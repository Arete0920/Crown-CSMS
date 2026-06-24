# Current Sandbox Endpoint

Date: 2026-06-23
Status: Internal sandbox endpoint corrected

## Verified Azure ownership

Azure CLI and portal verification confirmed the active subscription:

- Subscription: CROWN Christian School Management
- Subscription ID: `4ef0ba4b-4810-48d4-b3fe-953a9708953a`
- Tenant ID: `08597807-7a79-490b-87e5-83ae3e9d4b15`
- Resource group: `crown-rg`
- Static Web App: `crown-dash`
- Default hostname: `yellow-forest-0eecc8b0f.7.azurestaticapps.net`

## Current internal URLs

Use these for internal verification and operator testing:

- Frontend base: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
- Sandbox route: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/sandbox
- Login route: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/login
- Build metadata: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/build.json

## Invalid/stale URL

Do not use this URL for buyer, operator, or test access:

- https://crown-sandbox.azurestaticapps.net

Reason: Azure inventory for the verified CROWN subscription does not contain a Static Web App with this default hostname. Live probes returned HTTP 404 for `/`, `/build.json`, `/sandbox`, and `/login`.

## Buyer-facing rule

The `yellow-forest` default hostname is functional but not branded. It is acceptable only for internal emergency verification.

Before buyer distribution, configure and verify a branded custom domain on `crown-dash`, then update all invite links and operator runbooks to that branded domain.

## Required proof before buyer access

Buyer access remains NO-GO until current endpoint proof confirms:

- `/` returns HTTP 200 and loads CROWN.
- `/sandbox` returns HTTP 200 and loads the sandbox entry path.
- `/login` returns HTTP 200 and loads the login path.
- `build.json` reports the current deployed build metadata.
- Role login and role routing pass for School Admin, Teacher, Parent, and Student.
- No buyer-facing documentation references `crown-sandbox.azurestaticapps.net` as an active endpoint.

## Evidence references

- `audit-artifacts/sandbox-access-hotfix/20260623_194937-remediation-pack/03_url_probe.json`
- `audit-artifacts/sandbox-access-hotfix/20260623_194937-remediation-pack/04_decision.json`
- `audit-artifacts/sandbox-access-hotfix/20260623_194937-remediation-pack/05_internal_notice.txt`
