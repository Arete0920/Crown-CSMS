"""
analytics/tasks.py — Celery tasks for the analytics app.
"""
from __future__ import annotations

from datetime import date

from django.db.models import Count
from django.utils import timezone

from crown_api.celery_app import app


@app.task(name="analytics.tasks.refresh_all_health_scores", bind=True, max_retries=2, default_retry_delay=120)
def refresh_all_health_scores(self):
    """Recompute and persist CustomerHealth for every active school."""
    try:
        from core.models import School
        from analytics.services_health import upsert_customer_health

        school_ids = School.objects.values_list("id", flat=True)
        results = {}
        for school_id in school_ids:
            record = upsert_customer_health(school_id)
            results[str(school_id)] = record.overall_score
        return results
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)


def _build_historical_enrollment_data(school):
    from core.models import Enrollment

    rows = list(
        Enrollment.objects.filter(school=school)
        .values("academic_year__start_date")
        .annotate(enrollment=Count("id"))
        .order_by("academic_year__start_date")
    )
    return [
        {
            "date": row["academic_year__start_date"],
            "enrollment": row["enrollment"],
        }
        for row in rows
        if row.get("academic_year__start_date")
    ]


def _student_age(dob: date | None, today: date) -> int:
    if dob is None:
        return 0
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return max(years, 0)


def _build_retention_feature_data(school):
    from core.models import Student

    today = timezone.now().date()
    rows = []
    for student in Student.objects.filter(school=school).select_related("current_grade_level"):
        rows.append(
            {
                "grade_level_sort": getattr(student.current_grade_level, "sort_order", 0) or 0,
                "age_years": _student_age(student.dob, today),
                "is_active": 1 if student.status == "ACTIVE" else 0,
                "is_applicant": 1 if student.status == "APPLICANT" else 0,
                "retained": 1 if student.status in {"ACTIVE", "ALUMNI"} else 0,
            }
        )
    return rows


@app.task(name="analytics.tasks.run_all_predictive_models", bind=True, max_retries=2, default_retry_delay=300)
def run_all_predictive_models(self, tenant_id):
    """Run the conservative predictive analytics suite for one school tenant."""
    try:
        from analytics.predictors import run_enrollment_forecast, run_retention_risk
        from core.models import School

        school = School.objects.get(id=tenant_id)
        snapshot_date = timezone.now().date()

        historical_enrollment = _build_historical_enrollment_data(school)
        enrollment_result = run_enrollment_forecast(school, historical_enrollment)

        retention_features = _build_retention_feature_data(school)
        retention_result = run_retention_risk(school, retention_features)

        return {
            "school": school.name,
            "snapshot_date": str(snapshot_date),
            "runs_created": ["Enrollment Forecast", "Retention Risk"],
            "enrollment_forecast": enrollment_result,
            "retention_risk": retention_result,
        }
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)


@app.task(name="analytics.tasks.run_predictive_analytics_nightly")
def run_predictive_analytics_nightly():
    """Queue predictive analytics runs for every active school each night."""
    from core.models import School

    queued_for = []
    for school_id in School.objects.filter(is_active=True).values_list("id", flat=True):
        run_all_predictive_models.delay(str(school_id))
        queued_for.append(str(school_id))
    return {"queued_school_ids": queued_for, "count": len(queued_for)}
