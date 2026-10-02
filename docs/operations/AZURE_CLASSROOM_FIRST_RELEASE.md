# Azure classroom first hosted release

Azure is the selected destination. Crown is currently undeployed; merged classroom workflows and CI do not establish hosted operation. This procedure prepares the existing release path without provisioning resources, changing settings, activating payments or asserting production readiness.

## Read-only inventory

In an authenticated Azure CLI environment, identify the intended subscription and run:

```bash
python scripts/ops/azure_classroom_preflight.py \
  --subscription <subscription-id> \
  --resource-group crown-rg \
  --api-app crown-api-prod \
  --expected-sha <full-verified-release-sha> > azure-classroom-preflight.json
```

The collector uses only scoped read commands and selected metadata. It excludes app settings and credentials. Exit zero means collection completed, never release acceptance. Missing access exits two and preserves NOT VERIFIED. Store its output privately as release evidence, not in source control. Inventory the target subscription before creating replacement services; existing stopped resources may be reusable. No Azure resource, subscription, cost or credential has been verified by this document.

## Service configuration

| Service | Release requirement |
| --- | --- |
| API | Existing App Service deployment; exact immutable image; `/app/entrypoint.sh` checks migration currency before Gunicorn. |
| Dashboard | Existing SWA path; matching source and API origin; exact `dist/build.json`; SPA rewrites and authenticated routes. |
| PostgreSQL | Actual target database; controlled migrations; private access and accepted backup/restore evidence. |
| Broker | Functioning private Celery-compatible endpoint; TLS/auth configuration verified without exposing keys. |
| Worker | Same backend image and settings; `celery -A crown_api worker -l info`; registered `academics.tasks.prepare_family_notices`. |
| Beat | Same image and broker; one active scheduler; writable retained schedule state; task every fifteen minutes. |

The existing API workflow provisions neither worker nor beat. Select their Azure service types after inventory, including region, networking, identity, cost and supervision. Do not run them as unmanaged background processes inside the API container. Require schema currency before either starts. For beat, use a writable schedule path owned by the image's non-root user, for example `--schedule=/var/lib/celery/celerybeat-schedule` with a configured volume. A single replica does not by itself guarantee no overlap during revisions or deployments; stop the predecessor scheduler before activating its replacement.

Shared secrets/settings must resolve the same production `DATABASE_URL`, stable valid `DJANGO_SECRET_KEY`, `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`. Set `DJANGO_SETTINGS_MODULE=crown_api.settings`, `DJANGO_ENV=production`, `CROWN_ENV=production`, `DJANGO_DEBUG=false`, `DEBUG=false`, explicit allowed hosts and trusted/CORS origins. Verify the final effective settings and disable bootstrap/demo/open-session flags. Broker localhost defaults are not hosted connectivity evidence.

## Existing deployment path and boundaries

1. Re-resolve main, select a full verified source SHA, review applicable checks and retain the approved solo-developer evidence packet. PR #56 must be included; do not rebuild its classroom functionality.
2. Validate Azure staging first, as required by the GitHub-to-Azure operating model. Retain the exact source, environment and runtime results before production promotion.
3. Use an existing immutable `prod-deploy-*` tag in `.github/workflows/deploy-prod.yml` or its dispatch counterpart. Tag creation triggers deployment workflows; do not create one as a harmless preparation step.
4. The backend path calls `schema-migration-stage.yml` before deployment. Capture actual production execution of `migrate_with_lock`, `migrate --check` and `showmigrations --plan`; academics 0048 must be applied. Contract tests and test-database migration results are insufficient.
5. Build identity is currently baked by the Azure workflow into `backend/crown_api/build_info.py`. Require full SHA parity for configured image, baked identity and live API, plus worker/beat image digest. An app-setting value alone is insufficient.
6. Prefer a manual dashboard dispatch on the same immutable tag with `backend_deploy_tag` identifying that tag. The manual workflow builds non-tag refs with sandbox flags. The automatic tag path reads certified source from `docs/CURRENT_RELEASE_STATUS.md`, which currently asserts no successor source. Do not fabricate that field to unblock deployment; use the existing manual backend-tag resolution and retain true certification evidence.
7. Validate workflow secrets, variables, tenant identity and Azure permissions privately. Deployment app-setting changes are allowlisted; this preparation does not expand the allowlist or put infrastructure secrets into it.

## Runtime acceptance

- Correlate a naturally scheduled beat publication with worker receipt and successful completion using the same task ID. Manual task invocation does not prove beat.
- Capture digest and upcoming conference notice rows for controlled validation accounts. Inspect `school_id`, account, source key and availability; repeat the task and confirm one row per `(school_id, account_id, source_key)`, including after service restart.
- Verify disabled preferences, quiet hours, inactive accounts and restricted guardians. Notice rows and authorized UI reads are the proof; successful task counters alone are insufficient. This workflow creates in-app notices, not email/SMS.
- Validate teacher publishing/feedback/attendance, student draft/receipt/revision, parent verified-child/conference/notices, administrator source-defined coverage/attendance/support, and board aggregate-only reporting. Include cross-school, unrelated account, restricted guardian and expired/revoked substitute denials.
- Retain monitoring, restore/rollback evidence and final release control-path disposition. Update canonical release status and classroom deployment state only after observed acceptance. Payment processing remains disabled under current release authority.

## Preparation checks

```bash
python -m unittest discover -s scripts/ops -p test_azure_classroom_preflight.py -v
```

These tests verify read-only collection, blocked access, secret-safe errors and withheld certification. They are not Azure runtime tests.

References: [release authority](../CURRENT_RELEASE_STATUS.md), [classroom register](../CLASSROOM_EXPERIENCE.md), [operating model](../governance/CROWN_GITHUB_AZURE_OPERATING_MODEL.md), [recovery path](PRODUCTION_RECOVERY_PATH.md), [Microsoft App Service configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-common), [Azure CLI webapp reference](https://learn.microsoft.com/en-us/cli/azure/webapp).
