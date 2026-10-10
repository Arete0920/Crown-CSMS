# CROWN Azure Free-First Cost Controls

**Decision status:** Proposed operational cost controls; no production Azure resources changed.
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

## Budget alerts

In Azure Portal -> Cost Management -> Budgets, create a **$10 USD monthly initial alert budget** for the selected subscription with alerts at 50%, 80%, and 100%, addressed to the authorized subscription owner. Verify an accurate charge currency and billing scope before creation. This is a monitoring threshold rather than an instruction to stop workloads. The audit is read-only and intentionally does not create the budget without validated billing identity.

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
