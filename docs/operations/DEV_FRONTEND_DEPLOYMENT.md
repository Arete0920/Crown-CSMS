# DEV frontend deployment boundary

The dashboard deployment workflow's DEV preview path defaults `dev_deploy_only`
to **true**. Select `dev_certification_preview=true` and supply the full accepted
`dev_source_sha` already running on the DEV API. Production tag deployment is a
separate existing path and is unaffected by this input.

In deployment-only mode the workflow builds the pinned frontend, uploads it to
the existing `dev-certification` SWA preview, and verifies frontend build identity,
API artifact/build identity, database health, and existing credentialed CORS.
It does not configure API CORS/CSRF, run browser journeys, or prepare synthetic
schools, actors, or tokens. A missing existing CORS configuration fails the check;
it is not repaired by deployment-only execution.

This mode establishes deployment identity and basic connectivity only. It does
not establish owner-console, household, provisioning or tenant-isolation
acceptance. The workflow summary explicitly records those evidence limits.

Setting `dev_deploy_only=false` opts into the existing broader certification path,
including API CORS/CSRF settings changes, browser writes, and synthetic tenant
preparation. Dispatch that mode only with separately authorized scope. A workflow
input is an execution control, not proof of owner authorization.

Both modes still require the existing DEV environment/control path and explicit
deployment authority. No production deployment, payment activation, credential
rotation, or live-school provisioning is granted by this document. Roll back the
frontend by deploying its previously accepted source with a compatible verified
DEV backend; revert the workflow change through a governed PR if needed.

## Hosted fictional Jireh frontend preview (explicit DEV-only opt-in)

The manual dashboard workflow offers `dev_hosted_jireh_preview`, default **false**.
Only an explicitly selected `dev_certification_preview=true` build can set
`VITE_HOSTED_JIREH_DEMO=1`; the production job rejects this option. An
ordinary DEV preview build sets the flag to `0`, preserving prior behavior.

The flag affects only display/routing for isolated fictional Jireh Aid and
partner-SGO buyer pages. It does **not** configure or authorize the backend
`CROWN_HOSTED_JIREH_DEMO_ENABLED` gate, issue invitations, provision fictional
schools, grant SGO processor authority, execute migrations, or enable payments.
The backend remains default-off and requires independently authorized, verified
DEV-only configuration plus bound invitations and role/partner/guardian checks.
Do not use this input for production or assume a frontend build proves hosted
workflow acceptance. Keep issue #427 NO-GO until an approved exact-source
backend/frontend release and authenticated five-module transaction evidence.
