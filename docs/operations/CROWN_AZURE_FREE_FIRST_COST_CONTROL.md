# CROWN Azure Free-First Cost Controls

**Decision status:** Owner-approved free-first, no-surprise-spend governance (October 11, 2026). Live Azure budget configuration and actual spend remain UNVERIFIED; no production Azure resources changed by this document.
**Baseline:** October 10, 2026; repository `Arete0920/Crown-CSMS`.

## Immediate policy

- Retain the existing Azure Pay-As-You-Go subscription. It is not inherently a paid service tier for every resource.
- Target an essentially $0 demonstration environment using free allocations where practical, not a $0 guarantee.
- Protect `crown-api-prod`, its data, backups, secrets, managed identity, database, and exact-head release controls. Do not resize, migrate, stop, or delete these resources based solely on price.
- Existing production deployment workflows use Azure App Service, Azure Container Registry `crownregistry`, and Azure Static Web Apps. Do not silently replace these with Container Apps or free App Service.
- Free F1 App Service has constraints and is **not** a drop-in hosting replacement for CROWN's current Linux custom-container deployment. Container Apps consumption would require a separate documented architecture and delivery migration.
- Free Azure Static Web Apps is appropriate for a small demonstration if quotas and limitations are acceptable; no production SLA claim follows.
- PostgreSQL is a real persistence dependency. Never presume the first-12-month free promotion applies to an existing subscription. No real school PII in an unqualified demo.
- Budget alerts are not hard spending caps for Pay-As-You-Go.

## Collect evidence privately

From authenticated Azure Cloud Shell Bash:

```bash
python3 scripts/ops/crown_azure_cost_audit.py --resource-group crown-rg --output crown_azure_cost_report.json
```

Do not upload the report to public GitHub. The script reads the selected subscription's month-to-date and last-month costs, relevant resource SKUs, and existing budgets, then explicitly marks inaccessible information UNKNOWN. It does not authorize a release or certify runtime readiness.

Review Cost Management + Billing -> Cost Analysis separately with a **resource** grouping, including other resource groups, reservations, and subscriptions where relevant.

## Decision gates

1. **Inventory:** Confirm active subscription, resource group, current plan SKUs, database state, and all service dependencies.
2. **Costs:** Obtain actual last-month and current charges. No billing data = not verified, **not $0**.
3. **Classification:** Label each resource PROD/DEV/DEMO/UNKNOWN using live ownership and dependency evidence.
4. **Recovery:** Obtain verified backup/restore and rollback evidence before any production change.
5. **Savings proposals:** Prefer eliminating provably idle *nonproduction* duplicate infrastructure or moving **new demos** to eligible free service tiers. Estimate savings only from actual measured or published prices in the correct region.
6. **Change:** Use a single reversible infrastructure PR/runbook at a time with owner-approved execution and an auditable before/after cost and runtime comparison.
7. **Safety:** Never put production school data, financial records, or secrets into an unsecured free demo. Preserve tenant isolation, RBAC, and operational logging.

## Budget alerts and mandatory controls

The **$10 USD monthly budget** is a provisional *early-warning alert* for a new, nearly free demonstration subscription only, **not** an approved production spending allowance, spending cap, or asserted current run-rate. If existing services already cost more, first establish the real billing baseline and obtain the owner's actual monthly ceiling before setting an operationally meaningful subscription budget. Do not silently raise the ceiling.

After validating the current subscription, billing scope, currency, owner notification address, and real run-rate, configure **actual-cost alerts at 50%, 80%, and 100%** of the owner-approved monthly budget, plus a **forecast alert**, where available. Configure subscription **cost anomaly alerts** and a **daily saved Cost Analysis email** to the owner. Test alert delivery and record configuration evidence privately. Azure Cost Management data and notifications can lag; alerts alone are **not hard caps** and must never be described as guaranteed protection against charges.

Do not auto-stop, auto-delete, or auto-downsize the production API, PostgreSQL, registry, secrets, identity, or backups. A separate, reviewed resource-group-scoped nonproduction response may be authorized only after dependency classification and tested restore/recovery. Where supported, propose Azure Policy deny assignments to prevent **new** unapproved expensive SKUs/resource types, after audit-mode evaluation and review of existing resources. Deny policy is not a substitute for budget alerts or a universal hard spending cap.

## Mandatory cost approval gate for all new Azure resources or changes

Treat financial safety as an explicit **NO-GO gate**, including changes initiated through the portal, CLI, templates, or GitHub Actions. Before any change that could add recurring costs or increase usage, document:

1. **Identity and baseline:** verified subscription/billing currency, current month to date, preceding full month, current service and resource SKU, region, and whether any account credits/free-grant eligibility actually apply.
2. **Scope:** DEV, DEMO, or PROD; ownership and resource group; impact on current deployment, security, tenants, backups, and rollback.
3. **Monthly estimate:** the incremental *and total expected monthly* charges for compute, database, storage/backup, registry, logging/monitoring, network egress, messaging, and dependent services; specify upper-bound assumptions for plausible traffic and full-month uptime. Mark unverifiable amounts **UNKNOWN**, never $0.
4. **Alternatives:** test an eligible free/consumption option or reuse an existing resource before requesting a new paid resource; document feature, SLA, security, and migration limitations.
5. **Approval:** obtain an explicit owner-approved maximum monthly total and approval of any increase in recurring charges; do **not** provision or upgrade before that approval. No approval = NO-GO, even if infrastructure checks pass.
6. **Verification:** after an approved change, re-run a private inventory, check itemized Cost Analysis and forecasts after billing catches up, verify the app still works, and record actual-versus-estimate variance.

Keep paid resources at the smallest proven safe SKU, minimum necessary replica count, region appropriate for the service and data, bounded telemetry retention, bounded log ingestion, and only the storage/backup required for security and restoration. No speculative Premium/Enterprise upgrades, redundant demo environments, persistent idle workers, unbounded scale-out, or always-on capacity merely for convenience.

**Escalation:** At 50% actual-budget consumption, inspect spending; at 80% or a forecast over the monthly ceiling, freeze discretionary new paid deployments and investigate; at 100%, escalate immediately to the owner and prepare a *reviewed* cost-reduction response for nonproduction first. Never remove backups, weaken security controls, or disrupt production school service automatically. Reconcile charges, invoices, payment status, and forecast separately to reduce the risk of account suspension; an alert cannot guarantee funds or uninterrupted service.

## Verification status as of October 11, 2026

- **Verified in the repository:** this cost policy, the read-only cost-audit script, and the existing application deployment architecture.
- **NOT VERIFIED in the live subscription:** actual current and historic charges, SKU inventory, free credits, budget existence, alert recipients/delivery, anomaly alerts, and monthly affordability ceiling.
- **External step remaining:** run the approved read-only collection from an authenticated Azure session, inspect Cost Analysis at the subscription scope, and configure/verify budgets and alerts using verified billing identity. Keep detailed billing evidence outside the public GitHub repository.

## Relevant current files

- `.github/workflows/deploy-dev.yml`
- `.github/workflows/deploy-prod.yml`
- `.github/workflows/deploy-dashboard.yml`
- `.github/workflows/azure-classroom-preflight.yml`
- `docs/CURRENT_RELEASE_STATUS.md`
- `scripts/ops/crown_azure_cost_audit.py`

## Reference documents

- https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets
- https://learn.microsoft.com/en-us/azure/container-apps/billing
- https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans
- https://azure.microsoft.com/en-us/pricing/details/app-service/static/
