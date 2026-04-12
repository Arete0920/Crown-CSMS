# Crown Discernment Runtime Review

## Scope

This was a **runtime review only** of Crown Discernment analytics code.
No production integration was approved in this pass, and no new dashboards, endpoints, schema changes, or active runtime rollout were authorized.

## Files Reviewed

- `backend/analytics/predictors.py`
- `backend/analytics/tasks.py`

## Executive Verdict

The current analytics code is **directionally useful as conceptual-only work**, but it was **not safely isolated as written**. It gave misleading production-readiness signals by auto-linking outputs into Crown Compass / Solomon surfaces and by exposing a nightly task path that could queue predictive runs across active schools. Canon alignment is **partial at best**: Discernment is treated as an engine, but the current runtime behavior still blurs the boundary between conceptual analytics and live product integration.

## Findings by File

### `backend/analytics/predictors.py`

#### Strengths

- Uses clear conceptual model groupings for enrollment forecasting, retention indicators, and academic early warning.
- Persists model runs to `PredictiveModelRun`, which is a good foundation for later auditability.
- Uses explainability-oriented techniques such as SHAP or fallback feature-importance summaries.
- Fails relatively conservatively when optional dependencies or minimum data thresholds are not available.

#### Risks

- The file automatically finalizes runs into downstream product surfaces, which previously created live-feeling integration signals.
- Hard-coded thresholds and output shaping are not governance-versioned.
- Output language is stronger than the current canon approval level.
- The code stores run outputs, but not enough governance metadata for board-safe use.

#### Canon alignment issues

- Discernment is appropriately named as an analytics engine, but `_finalize_run()` was originally auto-linking outputs into **Crown Compass** and **Solomon** artifacts.
- That behavior blurred canon boundaries by making conceptual analytics look production-integrated.
- Solomon is supposed to be the guidance layer, not an automatically published analytics sink.

#### Model logic issues

- **Retention direction risk:** the model predicts `retained`, but `high_risk_count` is derived from `predict_proba(... )[:, 1] < 0.35`; this may be directionally correct, but the threshold is hard-coded, undocumented, and not governance-controlled.
- **Label leakage risk:** `_build_retention_feature_data()` includes `is_active` as a feature while also deriving `retained` from status values, which creates circular or tautological signal risk.
- **Fragile school-facing assumptions:** age, grade sort order, and simple status flags are too thin for confident retention interpretation.
- **Academic model overstatement:** `run_academic_risk()` reports `accuracy` from `model.score(X, y)` on the same fitted dataset, which inflates confidence.
- Minor naming issue: `PROPHT_MODEL_TYPE` is misspelled, which weakens polish and trust.

#### Explainability/governance issues

- Directionally good: SHAP/global feature importance is the right kind of explainability pattern for later governed use.
- Not yet governance-safe: there is no persisted threshold version, feature-set version, model version, policy-parameter version, or approval state in the output payload.
- Recommended actions are useful as placeholders, but they are not yet institution-defined, policy-approved, or review-gated.

#### Required later-phase changes

- Replace hard-coded thresholds with governance-defined configuration and versioning.
- Remove leakage-prone labels/features and define approved training labels explicitly.
- Add model/version/threshold metadata required for auditable runs.
- Require human review before any Solomon or Compass-facing publication.
- Narrow the first approved scope before any school-facing use.

#### Status classification

Status: **NEEDS MINIMAL SAFETY GUARD EDITS**

### `backend/analytics/tasks.py`

#### Strengths

- Tenant-oriented task structure is straightforward and readable.
- Retry behavior is present for task failures.
- The orchestration flow is simple enough to refactor safely later.

#### Risks

- The file contained a clear path to run predictive models across every active school.
- It is coupled to Celery scheduling and therefore could imply unauthorized production rollout.
- It calls the predictor functions that persist runs and, before this pass, linked outputs into Crown Compass / Solomon surfaces.

#### Canon alignment issues

- The task names and docstrings leaned toward active operational analytics rather than canon-gated conceptual review.
- The nightly task especially suggested Discernment was already an approved runtime capability inside the platform.

#### Execution risk issues

- `run_predictive_analytics_nightly()` queues predictive runs for **every active school**.
- `backend/crown_api/settings.py` includes a Celery beat entry for `analytics.tasks.run_predictive_analytics_nightly`, which means the code path was not merely theoretical.
- There was no explicit runtime hold or approval flag before this pass.

#### Required later-phase changes

- Keep predictive execution behind an explicit approval flag until governance sign-off exists.
- Review and remove or defer the beat schedule in `backend/crown_api/settings.py` during a separate runtime pass.
- Audit all direct callers, including `backend/financial_aid/workflows.py`, before any later approval.
- Define a manual-only v1 execution path before considering any automated orchestration.

#### Status classification

Status: **NEEDS MINIMAL SAFETY GUARD EDITS**

## High-Risk Issues

1. `backend/crown_api/settings.py` schedules `analytics.tasks.run_predictive_analytics_nightly`, creating a real automatic-execution path for conceptual analytics.
2. `backend/analytics/predictors.py` was auto-linking model outputs into `BoardExecutiveMetric` and Solomon `HelpArticle` content, which made the work look production-integrated.
3. The retention model has leakage and interpretability risk because `retained` is derived from status while status-derived features are also used as inputs.
4. Probability thresholds are hard-coded and not governance-defined, versioned, or school-approved.
5. The academic-risk path reports in-sample accuracy, which can create misleading confidence if shown to school users.

## Safe-to-Keep Conceptual Elements

- `PredictiveModelRun` persistence as a future audit trail foundation
- Enrollment forecasting as a future narrow-scope use case
- SHAP / global feature-importance summaries as directionally appropriate explainability tooling
- Conservative dependency/data-availability fallbacks
- Recommended-actions scaffolding as a later human-reviewed Solomon-support concept

## Recommended Minimal Safety Edits

- Added explicit conceptual-hold warning text at the top of `backend/analytics/predictors.py` and `backend/analytics/tasks.py`.
- Added a default-off runtime gate using `ENABLE_DISCERNMENT_RUNTIME` so predictive task execution and Compass/Solomon linking do not proceed unless explicitly enabled.
- Kept the changes confined to analytics safety isolation only; no new endpoints, no schema changes, and no dashboard wiring were added.

## Not Approved For Production

Crown Discernment remains **conceptual and canon-gated**. It is not approved for production integration, automated execution, live dashboard refresh, or autonomous school-facing decision support in its current state.

## Smallest Safe Next Step

Keep the new safety hold in place, then perform a separate runtime review of downstream callers and scheduling (`backend/crown_api/settings.py`, `backend/financial_aid/workflows.py`, and any board/dashboard linkage) before defining a narrow governance-approved v1 scope.
