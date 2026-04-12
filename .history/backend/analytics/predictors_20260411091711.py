"""
analytics/predictors.py — Crown Discernment conceptual runtime helpers.

Safety note: this module is canon-gated and not approved for production-integrated
Compass/Solomon execution unless an explicit runtime flag is enabled.
"""
from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Any

import numpy as np
from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone
from django.utils.text import slugify

from analytics.models import PredictiveModelRun

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None

try:
    import shap
except Exception:  # pragma: no cover - optional dependency
    shap = None

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - optional dependency
    Prophet = None

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
except Exception:  # pragma: no cover - optional dependency
    RandomForestClassifier = None
    LogisticRegression = None
    roc_auc_score = None
    train_test_split = None

ENROLLMENT_MODEL_NAME = "Enrollment Forecast"
RETENTION_MODEL_NAME = "Student Retention Risk"
ACADEMIC_MODEL_NAME = "Academic Risk Early Warning"
PROPHT_MODEL_TYPE = "Prophet"
LOGISTIC_MODEL_TYPE = "Logistic Regression + SHAP"
RANDOM_FOREST_MODEL_TYPE = "Random Forest + SHAP TreeExplainer"
LINEAR_FALLBACK_TYPE = "Linear Trend Fallback"
HEURISTIC_FALLBACK_TYPE = "Heuristic Fallback"
DISCERNMENT_RUNTIME_HOLD_MESSAGE = (
    "Crown Discernment remains conceptual / canon-gated and is not approved "
    "for production integration."
)


def _discernment_runtime_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_DISCERNMENT_RUNTIME", False))


def _to_dataframe(rows: Any, required_columns: list[str]):
    if rows is None:
        if pd is None:
            return []
        return pd.DataFrame(columns=required_columns)

    if pd is not None and isinstance(rows, pd.DataFrame):
        df = rows.copy()
    elif pd is not None:
        df = pd.DataFrame(list(rows))
    else:
        df = list(rows)

    if pd is not None:
        for column in required_columns:
            if column not in df.columns:
                df[column] = None
    return df


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _persist_run(
    *,
    model_name: str,
    school,
    output_json: dict[str, Any],
    feature_importance: list[dict[str, Any]] | dict[str, Any] | None = None,
    confidence_interval_low: float | None = None,
    confidence_interval_high: float | None = None,
) -> PredictiveModelRun:
    return PredictiveModelRun.objects.create(
        model_name=model_name,
        school=school,
        input_snapshot_date=timezone.now().date(),
        output_json=output_json,
        confidence_interval_low=confidence_interval_low,
        confidence_interval_high=confidence_interval_high,
        feature_importance=feature_importance,
    )


def _build_recommended_actions(model_name: str, output_json: dict[str, Any]) -> list[str]:
    top_features = [
        str(item.get("feature"))
        for item in (output_json.get("global_feature_importance") or [])[:3]
        if item.get("feature")
    ]

    if model_name == RETENTION_MODEL_NAME:
        actions = [
            "Review the flagged students with attendance, grade, and student-care teams this week.",
            "Use Solomon guidance to align family outreach, tutoring, and follow-up next steps.",
            "Open or refresh intervention notes for students with multiple risk drivers.",
        ]
    elif model_name == ENROLLMENT_MODEL_NAME:
        actions = [
            "Compare the forecast to reenrollment goals and the current admissions pipeline.",
            "Confirm staffing, billing, and aid readiness for the projected enrollment range.",
        ]
    else:
        actions = [
            "Review the highest-risk students with teachers and support staff for early intervention.",
            "Prioritize tutoring, mentoring, and family communication for the flagged cases.",
        ]

    if top_features:
        actions.append(f"Pay special attention to these current drivers: {', '.join(top_features)}.")

    return actions


def _link_run_to_solomon(run: PredictiveModelRun) -> str | None:
    try:
        from onboarding.models_tasks import HelpArticle
    except Exception:
        return None

    output = run.output_json or {}
    actions = _build_recommended_actions(run.model_name, output)
    top_features = [
        str(item.get("feature"))
        for item in (output.get("global_feature_importance") or [])[:3]
        if item.get("feature")
    ]

    detail_lines = []
    if output.get("high_risk_count") is not None:
        detail_lines.append(
            f"Students currently flagged for proactive support: {int(output.get('high_risk_count') or 0)}."
        )
    if output.get("next_year_total") is not None:
        detail_lines.append(f"Projected next-year enrollment: {int(output.get('next_year_total') or 0)} students.")
    if top_features:
        detail_lines.append(f"Top current drivers: {', '.join(top_features)}.")

    content = "\n\n".join(
        [
            (
                f"Crown Discernment recorded the latest {run.model_name} run for {run.school.name}. "
                "Use this article to review the explainable factors and recommended next steps."
            ),
            "\n".join(detail_lines) if detail_lines else "",
            "Recommended actions:\n- " + "\n- ".join(actions),
        ]
    ).strip()

    article_slug = {
        RETENTION_MODEL_NAME: "crown-discernment-retention-risk",
        ENROLLMENT_MODEL_NAME: "crown-discernment-enrollment-forecast",
        ACADEMIC_MODEL_NAME: "crown-discernment-academic-risk",
    }.get(run.model_name, f"crown-discernment-{slugify(run.model_name)}")

    try:
        article, _ = HelpArticle.objects.update_or_create(
            slug=article_slug,
            defaults={
                "title": f"Crown Discernment: {run.model_name}",
                "content": content,
                "module": "analytics",
                "published": True,
            },
        )
    except DatabaseError:
        return None
    return article.slug


def _link_run_to_compass(run: PredictiveModelRun) -> bool:
    try:
        from signals.models import BoardExecutiveMetric
    except Exception:
        return False

    output = run.output_json or {}
    metric, _ = BoardExecutiveMetric.objects.get_or_create(
        school=run.school,
        as_of_date=timezone.localdate(),
    )

    highlights = list(metric.highlights or [])
    watchlist = list(metric.watchlist or [])
    top_features = [
        str(item.get("feature"))
        for item in (output.get("global_feature_importance") or [])[:2]
        if item.get("feature")
    ]

    if run.model_name == ENROLLMENT_MODEL_NAME:
        summary = f"Crown Discernment forecast projects {int(output.get('next_year_total') or 0)} students next year."
        target = highlights
    elif run.model_name == ACADEMIC_MODEL_NAME:
        count = int(output.get("high_risk_count") or 0)
        summary = f"Crown Discernment flagged {count} student(s) for academic support this period."
        target = watchlist if count else highlights
    else:
        count = int(output.get("high_risk_count") or 0)
        summary = f"Crown Discernment flagged {count} student(s) for retention support."
        target = watchlist if count else highlights

    feature_note = f"Top discernment drivers: {', '.join(top_features)}." if top_features else ""

    if summary not in target:
        target.append(summary)
    if feature_note and feature_note not in highlights:
        highlights.append(feature_note)

    metric.highlights = highlights[:10]
    metric.watchlist = watchlist[:10]
    metric.save(update_fields=["highlights", "watchlist"])
    return True


def _finalize_run(model_run: PredictiveModelRun, result: dict[str, Any]) -> dict[str, Any]:
    result["recommended_actions"] = _build_recommended_actions(model_run.model_name, result)

    if not _discernment_runtime_enabled():
        result["solomon_linked"] = False
        result["crown_compass_refreshed"] = False
        result["integration_status"] = "hold"
        result["integration_hold_message"] = DISCERNMENT_RUNTIME_HOLD_MESSAGE
        model_run.output_json = result
        model_run.save(update_fields=["output_json"])
        return result

    article_slug = _link_run_to_solomon(model_run)
    compass_refreshed = _link_run_to_compass(model_run)
    result["solomon_linked"] = bool(article_slug)
    if article_slug:
        result["solomon_article_slug"] = article_slug
    result["crown_compass_refreshed"] = compass_refreshed

    model_run.output_json = result
    model_run.save(update_fields=["output_json"])
    return result


def _linear_enrollment_fallback(df) -> dict[str, Any]:
    if pd is None or getattr(df, "empty", True):
        return {
            "next_year_total": 0,
            "confidence_interval": [0, 0],
            "model_type": LINEAR_FALLBACK_TYPE,
        }

    ordered = df.sort_values("date")
    enrollment_values = [int(value) for value in ordered["enrollment"].fillna(0).tolist()]
    latest_value = enrollment_values[-1] if enrollment_values else 0

    if len(enrollment_values) > 1:
        deltas = [current - previous for previous, current in zip(enrollment_values[:-1], enrollment_values[1:])]
        avg_delta = mean(deltas)
    else:
        avg_delta = 0

    projected = max(0, round(latest_value + avg_delta))
    spread = max(1, round(abs(avg_delta) * 2))
    return {
        "next_year_total": int(projected),
        "confidence_interval": [int(max(0, projected - spread)), int(projected + spread)],
        "model_type": LINEAR_FALLBACK_TYPE,
    }


def _extract_positive_class_values(shap_values) -> np.ndarray:
    if isinstance(shap_values, list):
        values = np.asarray(shap_values[1] if len(shap_values) > 1 else shap_values[0])
    else:
        values = np.asarray(shap_values)

    if values.ndim == 3:
        return values[:, :, 1] if values.shape[-1] > 1 else values[:, :, 0]
    return values


def _top_feature_records(columns, raw_importance, top_n: int = 5) -> list[dict[str, Any]]:
    if pd is None:
        ranked_pairs = sorted(
            ((str(column), float(value)) for column, value in zip(columns, raw_importance)),
            key=lambda item: item[1],
            reverse=True,
        )
        return [{"feature": feature, "importance": importance} for feature, importance in ranked_pairs[:top_n]]

    frame = pd.DataFrame(
        {
            "feature": list(columns),
            "importance": [float(value) for value in raw_importance],
        }
    ).sort_values("importance", ascending=False)
    return frame.head(top_n).to_dict("records")


def run_enrollment_forecast(tenant, historical_data):
    """Prophet-based enrollment forecasting with conservative fallbacks."""
    df = _to_dataframe(historical_data, ["date", "enrollment"])

    if pd is None or getattr(df, "empty", True) or len(df) < 10:
        return {"error": "Not enough historical data"}

    df = df[["date", "enrollment"]].dropna().copy()
    if len(df) < 10:
        return {"error": "Not enough historical data"}

    df["date"] = pd.to_datetime(df["date"])
    df["enrollment"] = df["enrollment"].astype(int)

    if Prophet is None:
        fallback = _linear_enrollment_fallback(df)
        result = {
            "model_name": ENROLLMENT_MODEL_NAME,
            "next_year_total": fallback["next_year_total"],
            "confidence_interval_low": fallback["confidence_interval"][0],
            "confidence_interval_high": fallback["confidence_interval"][1],
            "trend": "up" if fallback["next_year_total"] >= int(df["enrollment"].iloc[-1]) else "down",
            "model_type": fallback["model_type"],
            "run_date": timezone.now().isoformat(),
        }
    else:
        prophet_df = df.rename(columns={"date": "ds", "enrollment": "y"})
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            uncertainty_samples=1000,
        )
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=365)
        forecast = model.predict(future)

        result = {
            "model_name": ENROLLMENT_MODEL_NAME,
            "next_year_total": int(forecast["yhat"].iloc[-1]),
            "confidence_interval_low": int(forecast["yhat_lower"].iloc[-1]),
            "confidence_interval_high": int(forecast["yhat_upper"].iloc[-1]),
            "trend": "up" if forecast["yhat"].iloc[-1] > forecast["yhat"].iloc[0] else "down",
            "model_type": PROPHT_MODEL_TYPE,
            "run_date": timezone.now().isoformat(),
        }

    model_run = _persist_run(
        model_name=ENROLLMENT_MODEL_NAME,
        school=tenant,
        output_json=result,
        confidence_interval_low=result.get("confidence_interval_low"),
        confidence_interval_high=result.get("confidence_interval_high"),
    )
    return _finalize_run(model_run, result)


def run_retention_risk(tenant, student_features):
    """Logistic regression retention scoring with SHAP-backed explanations."""
    df = _to_dataframe(student_features, ["retained"])
    if pd is None or getattr(df, "empty", True) or len(df) < 20 or "retained" not in getattr(df, "columns", []):
        return {"error": "Not enough student data"}

    X = df.drop(["retained"], axis=1).apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df["retained"].astype(int)
    if X.empty or y.nunique() < 2 or LogisticRegression is None or train_test_split is None or roc_auc_score is None:
        return {"error": "Retention model dependencies unavailable or data is not sufficiently labeled"}

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)

    if shap is not None and len(X_test) > 0:
        background_size = min(25, len(X_train))
        background = shap.kmeans(X_train, background_size)
        explainer = shap.KernelExplainer(model.predict_proba, getattr(background, "data", background))
        shap_sample = X_test.iloc[: min(50, len(X_test))]
        shap_values = explainer.shap_values(shap_sample, nsamples=min(100, max(10, len(shap_sample) * 2)))
        shap_matrix = _extract_positive_class_values(shap_values)
        raw_importance = np.abs(shap_matrix).mean(axis=0)
    else:
        shap_sample = X_test.iloc[: min(50, len(X_test))]
        raw_importance = np.abs(model.coef_[0])

    global_feature_importance = _top_feature_records(X.columns, raw_importance, top_n=len(X.columns))

    result = {
        "model_name": RETENTION_MODEL_NAME,
        "auc_score": round(float(auc), 3),
        "high_risk_count": int((model.predict_proba(X)[:, 1] < 0.35).sum()),
        "global_feature_importance": global_feature_importance,
        "model_type": LOGISTIC_MODEL_TYPE if shap is not None else "Logistic Regression",
        "run_date": timezone.now().isoformat(),
        "shap_summary": {
            "top_features": global_feature_importance[:5],
            "sample_rows_evaluated": int(len(shap_sample)),
        },
    }

    model_run = _persist_run(
        model_name=RETENTION_MODEL_NAME,
        school=tenant,
        output_json=result,
        feature_importance=global_feature_importance,
    )
    return _finalize_run(model_run, result)


def run_academic_risk(tenant, student_academic_data):
    """Random forest academic risk detection with TreeExplainer support."""
    df = _to_dataframe(student_academic_data, ["at_risk"])
    if pd is None or getattr(df, "empty", True) or len(df) < 30 or "at_risk" not in getattr(df, "columns", []):
        return {"error": "Not enough data"}

    X = df.drop(["at_risk"], axis=1).apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df["at_risk"].astype(int)
    if X.empty or y.nunique() < 2 or RandomForestClassifier is None:
        return {"error": "Academic risk model dependencies unavailable or data is not sufficiently labeled"}

    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    model.fit(X, y)

    if shap is not None:
        explainer = shap.TreeExplainer(model)
        shap_sample = X.iloc[: min(100, len(X))]
        shap_values = explainer.shap_values(shap_sample)
        shap_matrix = _extract_positive_class_values(shap_values)
        raw_importance = np.abs(shap_matrix).mean(axis=0)
    else:
        shap_sample = X.iloc[: min(100, len(X))]
        raw_importance = model.feature_importances_

    global_feature_importance = _top_feature_records(X.columns, raw_importance, top_n=len(X.columns))

    result = {
        "model_name": ACADEMIC_MODEL_NAME,
        "accuracy": round(float(model.score(X, y)), 3),
        "high_risk_count": int(model.predict(X).sum()),
        "global_feature_importance": global_feature_importance,
        "model_type": RANDOM_FOREST_MODEL_TYPE if shap is not None else "Random Forest",
        "run_date": timezone.now().isoformat(),
        "shap_summary": {
            "top_features": global_feature_importance[:5],
            "sample_rows_evaluated": int(len(shap_sample)),
        },
    }

    model_run = _persist_run(
        model_name=ACADEMIC_MODEL_NAME,
        school=tenant,
        output_json=result,
        feature_importance=global_feature_importance,
    )
    return _finalize_run(model_run, result)
