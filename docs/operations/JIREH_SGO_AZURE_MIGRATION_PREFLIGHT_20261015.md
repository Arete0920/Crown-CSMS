# Jireh SGO: Azure preflight and first website migration

**Date:** 2026-10-15  
**Status:** IN PROGRESS / NO DNS CUTOVER / NO AZURE RESOURCE PROVISIONED  
**Source:** public Arete Jireh SGO site and approved CROWN release guardrails  
**Current first-site candidate:** `sites/jireh-sgo/` (static informational site, no live SGO operations)

## Read-only evidence to capture in the owner's authenticated Azure session

Azure access is **not available from the current ChatGPT execution environment**. Do not claim tenant/subscription, budget, resource, identity, deployment or operational readiness until verified.

Use **Azure Cloud Shell** when signed in to the approved tenant. Read-only commands:

```bash
az account list --all --query "[].{name:name,id:id,state:state,isDefault:isDefault,tenantId:tenantId}" -o table
az account show --query "{name:name,id:id,state:state,tenantId:tenantId}" -o json
az group list --query "[].{name:name,location:location,managedBy:managedBy}" -o table
az resource list --query "[].{name:name,type:type,location:location,resourceGroup:resourceGroup}" -o table
az staticwebapp list --query "[].{name:name,resourceGroup:resourceGroup,sku:sku.name,defaultHostname:defaultHostname}" -o table
az webapp list --query "[].{name:name,resourceGroup:resourceGroup,state:state,defaultHostName:defaultHostName}" -o table
az monitor metrics alert list --query "[].{name:name,resourceGroup:resourceGroup,enabled:enabled}" -o table
az role assignment list --assignee "$(az account show --query user.name -o tsv)" --all -o table
```

Avoid exporting access tokens, credentials, connection strings, student data, or account secrets. Sensitive identifiers in captured outputs should be retained in owner-controlled systems, not a public GitHub issue. Verify Azure Cost Management > Cost analysis and Budgets, any expired promotional/free credits, actual spend to date, quotas, diagnostic logging, account recovery, security defaults and production billing alerts. Azure alerts do not enforce a spending stop.

## DNS and GoDaddy safety

- Export current A, AAAA, CNAME, TXT, NS, MX, SPF, DKIM, DMARC, verification and mail-autodiscovery records from the authoritative DNS provider.
- Confirm whether DNS is actually hosted at GoDaddy; registrar and DNS authority can differ.
- Verify the current Arete site is hosted in its ChatGPT Site project versus GoDaddy Website Builder. Avoid claiming a migration away from the wrong hosting source.
- Inventory subdomains, custom-domain ownership, certificate expiry, domain renewals, webmaster verification, redirects, sitemap, favicon and media.
- Preserve all email/DNS records. **Do not touch MX, SPF, DKIM, DMARC or mail autodiscovery.**
- Stage and test at an Azure-generated hostname; prevalidate a designated product hostname with TXT where supported before routing.
- Record TTL, existing records, screenshots and rollback owner. Keep old hosting paid and active during stabilization if required; no domain-wide nameserver cutover.

## Content inventory from public Jireh SGO page

- Brand/title and pilot/development status
- Description and grantor responsibilities
- Application, verification, human eligibility/award authority and coordination
- Six-step planned workflow
- Explicit compliance, financial and operational limitations
- SGO design/pilot-partner conversation CTA
- Related CROWN Jireh page
- Two-page PDF `/resources/jireh-sgo-overview.pdf`
- Original logo `/images/jireh-sgo/logo.png`
- Contact/phone/email, privacy and terms
- Site navigation and footer (retain institutional Arete identity, simplify product site)

**Content source URLs:**
- https://areteadvisorygroup.com/jireh-sgo
- https://areteadvisorygroup.com/resources/jireh-sgo-overview.pdf
- https://areteadvisorygroup.com/images/jireh-sgo/logo.png
- https://areteadvisorygroup.com/contact
- https://areteadvisorygroup.com/privacy
- https://areteadvisorygroup.com/terms

## Explicit gates

| Gate | State | Evidence |
| --- | --- | --- |
| Current source claims reconciled to Jireh SGO pilot-only foundation | PARTIAL | Product status and public copy inspected |
| Static replacement code and automated content safety tests | PREPARED | `sites/jireh-sgo/` |
| Official source PDF/logo archived and branding visually compared | BLOCKED | Source bytes unavailable in current runtime |
| Authenticated Azure subscription, RBAC, budgets and inventory | BLOCKED | No Azure credentialed connector/session |
| Historical GoDaddy DNS and mail-record export | BLOCKED | No DNS-management connection |
| Azure staging resource and certificate | NOT STARTED | Requires verified subscription and owner cost approval |
| Lead storage, notification, calendar workflow, anti-abuse | NOT STARTED | Current CTA hands off to existing Arete inquiry |
| Independent contact form delivery and persistence test | NOT VERIFIED | Must test with synthetic data |
| Accessibility, browser, security, redirects and performance suite | PARTIAL | Structural source checks only |
| Full backup/rollback practice | NOT STARTED | Requires live staging/runtime access |
| DNS cutover, old-host decommission | NOT AUTHORIZED | Must not occur during preparation |

## Planned smallest safe increments

1. Merge site-source-only PR after required GitHub gates; no production deploy.
2. Obtain Azure read-only inventory and signed-in DNS export; price the smallest eligible Static Web App; get explicit recurring-cost approval before anything billable.
3. Export original approved PDF and logo, check SHA-256 checksums and usage rights, copy to new site; remove legacy-host dependence for critical assets and legal pages.
4. Add durable first-party demo lead pipeline, acknowledgment, sales notifications, spam defense and audit logs; test failures and recoveries, without exposing student or applicant information.
5. Deploy to staging and verify mobile, accessibility, SEO, TLS, headers, caching, origin delivery, lead flow, deployment identity and rollback.
6. Perform controlled single product hostname cutover only after signoff; verify mail unaffected and 24–72h telemetry, then plan Diadem migration.

## Acceptance rule

Source tests and a merged PR are not an Azure deployment; staging deployment is not customer software activation; a DNS cutover is not a certified Jireh SGO production release. Fail closed on any missing evidence.
