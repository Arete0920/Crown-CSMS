# Azure / DevOps - Post-Deploy Proof Packet

> Authority Scope Notice (2026-05-29)
>
> This file is an operational post-deploy packet and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

Generated: 2026-05-01T02:33:33

## Status

Production release remains NO-GO until this packet passes.

## Required Gates

1. Backend health returns HTTP 200.
2. Backend health or metadata body shows the approved SHA.
3. Frontend root returns HTTP 200.
4. Frontend /build.json returns HTTP 200.
5. Frontend build metadata shows the approved SHA.
6. Browser smoke passes.
7. Runtime tenant and RBAC proof is complete.
8. Judgment Day gauntlet rerun improves score and has no release-killing P0.

## Approved SHA Target

b9dad81

## URLs

- Backend: https://crown-api-prod.azurewebsites.net/api/health/
- Frontend: https://crown-dash.azurestaticapps.net/
- Build proof: https://crown-dash.azurestaticapps.net/build.json

## Run

`powershell
powershell -ExecutionPolicy Bypass -File scripts\execution\270_post_azure_live_proof.ps1
`

