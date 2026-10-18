# Jireh Financial Aid — Azure staging candidate (NOT DEPLOYED)

First product website migration: **the entire Jireh financial-aid family**, not only Jireh SGO.

- Primary: CROWN Jireh mission-aligned school financial aid.
- Related pilot-development offering: Jireh SGO scholarship-grantor administration.
- Site source: `sites/jireh/index.html`
- Shared family-wide appearance: `sites/shared/product-theme.css`
- Built output: `sites/jireh/dist/` (generated; do not commit)
- **No Azure deployment, paid service or GoDaddy DNS change is authorized by this PR.**

## Build and test

```bash
node --test sites/jireh/tests/site.test.mjs
node sites/jireh/build.mjs
python3 -m http.server 8090 --directory sites/jireh/dist
```

Azure Static Web Apps build configuration when Azure inventory/budget approval and a deploy plan exist:

- app_location: `sites/jireh`
- app_build_command: `node build.mjs`
- output_location: `dist`
- api_location: unset (no demo registration API has been accepted)
- default domain until DNS/CNAME prevalidation and cost approval

## Migration source and uncompleted dependency list

Original site sources:
- https://areteadvisorygroup.com/jireh
- https://areteadvisorygroup.com/jireh-sgo
- https://areteadvisorygroup.com/resources/jireh-sgo-overview.pdf
- https://areteadvisorygroup.com/images/jireh-sgo/logo.png

The original imagery and downloadable PDF have NOT been fully exported or parity-verified. This site uses self-contained conceptual CSS/HTML hero artwork intentionally instead of a misleading screenshot. In the staged build, overview PDF, legal links and contact requests still point to the existing Arete website. Independently test the link targets and migrate/secure the original assets prior to main-site retirement.

The first-party lead/demo registration service is NOT implemented or certified; existing contact CTA is a transitional handoff, not a guaranteed booking. Confirm end-to-end persistence, acknowledgment, sales routing, calendar booking, consent, abuse prevention and fault recovery before claiming instant scheduling.

Required gates: read-only authenticated Azure subscription/RBAC/spend/alerts/quotas/resource inventory, GoDaddy authoritative DNS and email record export, security and audit review, source-asset ownership, functional QA, accessible desktop/mobile/browser verification, staging TLS, cost approval, and tested reversible single-hostname cutover. Do not conflate production-ready marketing with production-ready financial-aid processing.

## Exported source assets

The SGO PDF, the official SGO logo, and the CROWN family billing concept image are vendored in the site source and copied into the staging output by `build.mjs`. Confirm owner rights and visual parity in browser QA; `https://areteadvisorygroup.com/contact`, privacy and terms remain live links for the transition.


## Jireh hosting: execution gates and accepted Azure facts (15 Oct 2026)

**Source-controlled execution path:** Existing `.github/workflows/azure-classroom-preflight.yml` (manual dispatch on reviewed `main`; Azure federated identity, no new client secrets). Added `jireh_azure_site_preflight.py` performs only read-only Azure CLI commands and emits private, redacted evidence.

## Evidence collected from 12 Oct 2026 manual run

- GitHub Actions run 38247725456 authenticated successfully using federated Azure login and completed the resource-inventory collector.
- The owner subscription's `crown-rg` contained 26 Azure resources, including **one Static Web App** already assigned to CROWN's dashboard and existing production App Service infrastructure.
- Azure cost diagnostics returned **UNAVAILABLE/RATE_LIMIT** for month-to-date and last-month charges, and **UNAVAILABLE/AUTHENTICATION** on one budgets operation. **Do not interpret missing costs as $0 or proof of free eligibility.**
- The hosted production API health check answered HTTP 200 with database reported OK, but was not exact-head release parity for the Jireh website.
- Production CROWN runtime certification remained `NOT VERIFIED`; none of the historical preflight evidence authorizes payments, student financial data or a public Jireh portal.

## Precise next gated operations

1. On current main run **Azure Classroom Release Preflight** via GitHub Actions > Run workflow. Verify the new `jireh-azure-site-preflight-<SHA>` artifact together with existing costs/runtime artifacts. Treat unavailable fields as blocked.
2. In Azure Portal Cost Management (authenticated owner), confirm actual current and last month costs, subscription budgets, alert recipients, and eligibility for an additional **Free** Azure Static Web App (and any feature/quota restrictions). The current Free listing alone is not a sufficient approval.
3. Only after explicit approval of recurring charges, authorize a new isolated Jireh *staging* Static Web App. **Do not repurpose `crown-dash` or attach a new product site to its live resources.** Deploy only the committed `sites/jireh/dist` build to the Azure-assigned temporary hostname; disable search indexing.
4. Validate TLS, security headers, 320/375/768/1440px browser appearance, internal links, robots and CTA handling with seeded *synthetic* data; verify actual inquiry notification and persistence through Arete's existing contact workflow or a separately accepted registration backend.
5. Export the authoritative DNS zone and confirm who currently controls website hosting, domain, and email. Preserve existing MX, SPF, DKIM, DMARC and verification TXT records.
6. Choose the Jireh hostname, complete TXT/CNAME ownership verification, rehearse reversible DNS-only switch, and take formal launch approval. After confirmed live stability update Arete site links and condense duplicate content while retaining advisory articles.

**No public launch, resource provision, billable tier or DNS changes are authorized by this document.** No GitHub artifact substitutes for the owner's billing view or tested staging.


## Jireh one-shot isolated Free-tier Azure staging

This adds a deliberately bounded deployment job to the existing governed Azure preflight workflow. No separate workflow is created. On PRs the staging job is **skipped**. On main push it runs only if the exact merge commit message includes `[jireh-staging-free-once]`.

- Source: accepted main commit only; Jireh site built and local tests pass before modifying Azure.
- Authentication: existing GitHub Actions OIDC federation, no new client secret.
- Target: `crown-rg/jireh-site` in East US 2, SKU **Free only**, on an Azure-generated temporary `azurestaticapps.net` hostname.
- Before creation: validate the whole subscription's SWA inventory, recognized SKUs, ownership, and official 10-Free-sites subscription limit; refuse unknown or exhausted quota, paid existing instances, or conflicting ownership.
- After creation: validate returned SKU remains Free. Never operate on `crown-dash` or CROWN production API.
- Deployment uses an ephemeral masked SWA deployment token. No account IDs or tokens go to repository or GitHub artifacts.
- Release proof: HTTPS content, robots noindex, PDF, logo, and concept image bytes exactly match the committed source.
- No custom domain assignment, DNS update, GoDaddy record alteration, live payments, real school financial-aid PII, or application production certification.
- This does not resolve the earlier missing subscription-wide spending and budget visibility; paid tiers and broad production release remain blocked.

GitHub branch protection controls merging. A single authorized squash merge with that marker triggers the one-time free staging action. If Azure RBAC, quota, resource creation or deploy permission is missing, the job fails closed with a check result instead of guessing.

Official reference: https://learn.microsoft.com/en-us/azure/static-web-apps/quotas and https://learn.microsoft.com/en-us/azure/static-web-apps/static-web-apps-cli-deploy

## October 18 staging execution authorization

The owner has expressly requested immediate execution of the existing isolated Free-only Azure staging route. This change records the authorization to attempt the source-controlled one-shot staging job, **not** a claim of Azure deployment. After exact-head CI acceptance, merge this PR with a merge commit message containing `[jireh-staging-free-once]`. The job must fail closed if quota, RBAC, environment protection, Free SKU, or deployment verification fails. Do not change custom domains, Arete DNS or email, enable payments, or authorize a paid SKU. Confirm successful workflow execution and live site integrity before declaring Azure staging complete. Independent full migration/cutover approval remains separate.
