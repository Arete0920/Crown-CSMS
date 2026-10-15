# Jireh one-shot isolated Free-tier Azure staging

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
