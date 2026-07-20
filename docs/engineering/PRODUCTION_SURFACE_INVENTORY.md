# Production Surface Inventory

**Controlling issue:** #1453  
**Release authority:** #1374  
**Production authorization:** Not implied

## Purpose

`scripts/release/production_surface_inventory.py` creates deterministic JSON and Markdown inventories from the current repository source at one exact commit SHA. It maps each discovered surface to one supported proof method or approved exclusion and fails when a required domain is absent, an identifier is duplicated, a classification is unsupported, or any surface remains `UNMAPPED`.

## Canonical sources

The collector uses current source rather than historical scorecards:

- frontend routes: `frontend/dashboards/src/routes/paths.js`;
- dashboards: `frontend/dashboards/src/config/dashboardRegistry.js`, with `PATHS.*` resolution;
- wizards: `frontend/dashboards/src/routes/wizard-manifest.js`;
- wizard steps: named step arrays in current wizard source files;
- modules: Django `AppConfig` declarations in `backend/*/apps.py`;
- APIs and integration routes: Django's initialized URL resolver, recursively composing every include and dynamic wizard registration;
- background tasks: current `backend/**/tasks.py` functions and task decorators;
- integrations: composed integration, Microsoft identity, and IAM route entry points.

## Classification rules

Supported values are:

- `CRAWLER`
- `PLAYWRIGHT`
- `API_CONTRACT`
- `BACKEND_TEST`
- `OPERATIONAL_DRILL`
- `MANUAL_REVIEW`
- `EXCLUDED_PAYMENT_PROCESSING`
- `EXCLUDED_HANDOFF`
- `NOT_APPLICABLE`
- `UNMAPPED`

Routes, dashboards, wizards, modules, APIs, tasks, and integrations receive domain-specific proof assignments. Payment-processing and ownership-transfer boundaries are evaluated first. Missing dashboard paths, unsupported domains, and any surface without a supported rule remain `UNMAPPED`; `--fail-on-unmapped` makes that condition terminal.

Provider-neutral billing, ledger, invoice, balance, payment-record, and payment-plan surfaces remain in scope. Only external processing entry points are excluded.

## Outputs

The workflow uploads:

- `production-surface-inventory.json`;
- `production-surface-inventory.md`.

Both contain the exact repository SHA, a deterministic inventory digest, counts by domain and classification, source locations, stable identifiers, proof assignments, and explicit non-claims.

## Reproduction

```bash
python scripts/release/production_surface_inventory.py \
  --root . \
  --output-dir audit-artifacts/production-surface/current \
  --fail-on-unmapped
```

The `Production Surface Inventory` workflow checks out the pull-request head SHA rather than GitHub's synthetic merge identity, runs the focused tests, generates the packet, validates zero `UNMAPPED` rows, and retains the outputs as an artifact.

## Evidence boundary

A passing inventory proves deterministic discovery and classification at the recorded repository SHA. It does not prove that the mapped crawler, Playwright, API, backend, operational, or manual evidence has passed. It does not authorize production.
