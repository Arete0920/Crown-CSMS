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
