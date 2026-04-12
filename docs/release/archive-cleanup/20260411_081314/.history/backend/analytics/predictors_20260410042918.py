from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Any

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - optional dependency
    Prophet = None

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
except Exception:  # pragma: no cover - optional dependency
    LogisticRegression = None
    roc_auc_score = None
    train_test_split = None


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


def _linear_enrollment_fallback(df) -> dict[str, Any]:
    if pd is None or getattr(df, "empty", True):
        return {
            "next_year_total": 0,
            "confidence_interval": [0, 0],
            "model": "Linear Trend Fallback",
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
        "model": "Linear Trend Fallback",
    }


def run_enrollment_forecast(tenant, historical_data):
    """Prophet-first enrollment forecast with a deterministic fallback."""
    df = _to_dataframe(historical_data, ["date", "enrollment"])

    if pd is None or getattr(df, "empty", True):
        return {
            "next_year_total": 0,
            "confidence_interval": [0, 0],
            "model": "Prophet + Linear Trend",
            "school": getattr(tenant, "name", str(tenant)),
        }

    df = df[["date", "enrollment"]].dropna().copy()
    if df.empty:
        return {
            "next_year_total": 0,
            "confidence_interval": [0, 0],
            "model": "Prophet + Linear Trend",
            "school": getattr(tenant, "name", str(tenant)),
        }

    df["date"] = pd.to_datetime(df["date"])
    df["enrollment"] = df["enrollment"].astype(int)

    if Prophet is None or len(df) < 2:
        result = _linear_enrollment_fallback(df)
    else:
        prophet_df = df.rename(columns={"date": "ds", "enrollment": "y"})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=365)
        forecast = model.predict(future)
        result = {
            "next_year_total": int(round(forecast["yhat"].iloc[-1])),
            "confidence_interval": [
                int(round(forecast["yhat_lower"].iloc[-1])),
                int(round(forecast["yhat_upper"].iloc[-1])),
            ],
            "model": "Prophet + Linear Trend",
        }

    result["school"] = getattr(tenant, "name", str(tenant))
    return result


def _heuristic_retention_risk(df):
    if pd is None or getattr(df, "empty", True):
        return {
            "auc_score": None,
            "high_risk_students": 0,
            "feature_importance": {},
            "model": "Heuristic Fallback",
        }

    features = [column for column in df.columns if column != "retained"]
    if not features:
        return {
            "auc_score": None,
            "high_risk_students": 0,
            "feature_importance": {},
            "model": "Heuristic Fallback",
        }

    risk = pd.Series(0.5, index=df.index, dtype=float)
    feature_importance: dict[str, float] = {}
    for feature in features:
        series = pd.to_numeric(df[feature], errors="coerce").fillna(0)
        feature_importance[feature] = float(series.corr(df["retained"]).round(4)) if df["retained"].nunique() > 1 else 0.0
        if series.max() != series.min():
            normalized = (series - series.min()) / (series.max() - series.min())
            risk = risk - (normalized * 0.15)

    high_risk_students = int((risk < 0.3).sum())
    return {
        "auc_score": None,
        "high_risk_students": high_risk_students,
        "feature_importance": feature_importance,
        "model": "Heuristic Fallback",
    }


def run_retention_risk(tenant, student_features):
    """Retention risk scoring with sklearn when available and safe fallbacks otherwise."""
    df = _to_dataframe(student_features, ["retained"])
    if pd is None or getattr(df, "empty", True) or "retained" not in getattr(df, "columns", []):
        return {
            "auc_score": None,
            "high_risk_students": 0,
            "feature_importance": {},
            "model": "Logistic Regression",
            "school": getattr(tenant, "name", str(tenant)),
        }

    df = df.dropna(subset=["retained"]).copy()
    if df.empty:
        fallback = _heuristic_retention_risk(df)
        fallback["school"] = getattr(tenant, "name", str(tenant))
        return fallback

    y = df["retained"].astype(int)
    X = df.drop(columns=["retained"]).apply(pd.to_numeric, errors="coerce").fillna(0)

    if LogisticRegression is None or roc_auc_score is None or train_test_split is None or y.nunique() < 2 or len(df) < 5:
        fallback = _heuristic_retention_risk(pd.concat([X, y.rename("retained")], axis=1))
        fallback["school"] = getattr(tenant, "name", str(tenant))
        return fallback

    stratify = y if y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]) if len(X_test) else None

    result = {
        "auc_score": round(float(auc), 3) if auc is not None else None,
        "high_risk_students": int((probabilities[:, 1] < 0.3).sum()),
        "feature_importance": {column: float(weight) for column, weight in zip(X.columns, model.coef_[0])},
        "model": "Logistic Regression",
        "school": getattr(tenant, "name", str(tenant)),
    }
    return result
