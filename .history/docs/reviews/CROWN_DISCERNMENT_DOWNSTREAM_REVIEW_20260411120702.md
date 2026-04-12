# Crown Discernment Downstream Caller and Scheduler Review

## Scope

This pass reviewed downstream callers, scheduling, and board/dashboard coupling related to Crown Discernment.
It remained isolated: no new endpoints, no dashboard buildout, no schema changes, and no Crown Core architectural changes were introduced.

## Files Reviewed

- `backend/crown_api/settings.py`
- `backend/financial_aid/workflows.py`
- `backend/governance/services.py`
- `backend/board_oversight/api_governance.py`
- `backend/signals/api.py`
- `backend/governance/openapi.py`

## Executive Verdict

The highest remaining runtime risk was not in the model helpers themselves, but in **downstream orchestration and product-surface coupling**. A real scheduler entry exists in `backend/crown_api/settings.py`, and a direct Discernment caller existed in `backend/financial_aid/workflows.py`. Those patterns made conceptual analytics look closer to approved runtime behavior than canon allows.

## Key Findings

### 1. Scheduler risk in `backend/crown_api/settings.py`

- `CELERY_BEAT_SCHEDULE` still contains `analytics.tasks.run_predictive_analytics_nightly`.
- Because the analytics task layer is now default-held, this is no longer an immediate execution hazard.
- However, it is still a **misleading production-readiness signal** and should be reviewed in a future core-config pass.

### 2. Direct caller in `backend/financial_aid/workflows.py`

- `_run_discernment()` directly called `run_retention_risk()` during financial-aid processing.
- That created a concrete path for conceptual analytics to run inside an operational workflow.
- A minimal hold guard was added in this pass so the workflow now returns `status: "hold"` unless `ENABLE_DISCERNMENT_RUNTIME` is explicitly enabled.

### 3. Dashboard coupling in `backend/governance/services.py`

- `_latest_predictive_insight()` reads from `PredictiveModelRun` and feeds predictive summaries into governance/dashboard outputs.
- This is directionally aligned with Crown Compass eventually consuming Discernment outputs, but it is still **too close to live integration** for the current canon stage.
- No changes were made here in this pass to avoid changing production dashboard behavior.

### 4. Board and signals surface language

- `backend/board_oversight/api_governance.py` still exposes placeholder “Crown Compass executive summary” language.
- `backend/signals/api.py` still presents “Crown Compass 2.0” as an active board summary surface.
- These should be handled later in a separate runtime/product-surface cleanup, not in this isolated pass.

### 5. Runtime schema wording in `backend/governance/openapi.py`

- The runtime OpenAPI decorators still describe live governance and Crown Compass behavior.
- This remains a later-phase cleanup item because it touches runtime-facing schema metadata.

## Minimal Safety Edit Applied

### `backend/financial_aid/workflows.py`

A small safety hold was added so `_run_discernment()` does not execute analytics during aid processing unless `ENABLE_DISCERNMENT_RUNTIME` is explicitly enabled.

## Not Changed in This Pass

- `backend/crown_api/settings.py`
- `backend/governance/services.py`
- `backend/board_oversight/api_governance.py`
- `backend/signals/api.py`
- `backend/governance/openapi.py`

These were reviewed **read-only** and intentionally left untouched here.

## Smallest Safe Next Step

Keep the current default-off safety holds in place, then perform a separate, explicit runtime surface cleanup for scheduler configuration, governance/dashboard messaging, and any remaining live-integration language.
