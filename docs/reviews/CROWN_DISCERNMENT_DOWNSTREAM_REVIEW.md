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

- `CELERY_BEAT_SCHEDULE` contained `analytics.tasks.run_predictive_analytics_nightly` as a real scheduled path.
- In this pass, that schedule was placed behind the same `ENABLE_DISCERNMENT_RUNTIME` hold so it is no longer enabled by default.
- This reduces accidental execution risk, even though the broader scheduler surface should still be reviewed later.

### 2. Direct caller in `backend/financial_aid/workflows.py`

- `_run_discernment()` directly called `run_retention_risk()` during financial-aid processing.
- That created a concrete path for conceptual analytics to run inside an operational workflow.
- A minimal hold guard was added in this pass so the workflow now returns `status: "hold"` unless `ENABLE_DISCERNMENT_RUNTIME` is explicitly enabled.

### 3. Dashboard coupling in `backend/governance/services.py`

- `_latest_predictive_insight()` reads from `PredictiveModelRun` and feeds predictive summaries into governance/dashboard outputs.
- This is directionally aligned with Crown Compass eventually consuming Discernment outputs, but it was still **too close to live integration** for the current canon stage.
- In this pass, the service was updated to suppress predictive highlight/watchlist messaging whenever Discernment is still on hold.

### 4. Board and signals surface language

- `backend/board_oversight/api_governance.py` still uses placeholder summary logic, but its wording was softened in this pass to avoid implying approved Discernment integration.
- `backend/signals/api.py` no longer describes the board summary as an implicitly active “Crown Compass 2.0” predictive surface.
- These surfaces are still later-phase review items, but the most misleading wording has been reduced.

### 5. Runtime schema wording in `backend/governance/openapi.py`

- The runtime OpenAPI decorators previously described live governance and Crown Compass behavior in a way that overstated Discernment readiness.
- In this pass, the relevant descriptions were softened so predictive references are clearly treated as conceptual / hold-gated unless separately approved.

## Minimal Safety Edits Applied

- `backend/financial_aid/workflows.py` — added a safety hold so `_run_discernment()` does not execute analytics during aid processing unless `ENABLE_DISCERNMENT_RUNTIME` is explicitly enabled.
- `backend/crown_api/settings.py` — gated the predictive nightly schedule so it is no longer enabled by default.
- `backend/governance/services.py` — suppressed predictive highlight/watchlist messaging while Discernment remains on hold.
- `backend/signals/api.py` and `backend/governance/openapi.py` — softened runtime-facing wording so it no longer implies approved live predictive integration.
- `backend/board_oversight/api_governance.py` — clarified that the board summary helper remains a stored / placeholder surface rather than approved Discernment production behavior.

## Not Changed in This Pass

- No endpoints were added.
- No dashboard logic was expanded.
- No schema changes or Crown Core architectural moves were introduced.

## Smallest Safe Next Step

Keep the current default-off safety holds in place, then perform a separate, explicit runtime surface cleanup for scheduler configuration, governance/dashboard messaging, and any remaining live-integration language.
