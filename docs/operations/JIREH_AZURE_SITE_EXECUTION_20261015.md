# Jireh hosting: execution gates and accepted Azure facts (15 Oct 2026)

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
