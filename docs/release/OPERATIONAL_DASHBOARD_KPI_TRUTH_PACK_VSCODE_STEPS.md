# Operational Dashboard KPI Truth Pack - VS Code Verification Steps

## Branch

`release/operational-dashboard-kpi-truth-pack-current`

## Connector-completed scope

The connector branch adds:

- Shared operational KPI catalog.
- Shared dashboard operational model builder.
- Dashboard completeness verification script.
- Frontend npm verification script.
- Admissions dashboard Stage Aging Pressure KPI consumption.
- Evening release truth proof runner.

The current mainline already had page-level data truth, communication strip, and data truth status components. This branch preserves that newer mainline work rather than replacing it with duplicate banner components.

## Required local commands

Run from repository root in VS Code PowerShell:

```powershell
git fetch origin
git checkout release/operational-dashboard-kpi-truth-pack-current
git pull

cd frontend\dashboards
npm install
npm run verify:dashboard-completeness
npm run test -- --run
npm run build

cd ..\..
cd backend
python -m pytest applications/tests/test_admissions_endpoints.py -q

cd ..
powershell -ExecutionPolicy Bypass -File scripts/execution/220_evening_release_truth_proof.ps1
```

## Backend stage-aging patch still required locally

The frontend now consumes `rawSummary.stage_aging`. The backend endpoint must return it before the KPI can show true live values.

File: `backend/applications/views_admissions.py`

Add this helper after `_build_velocity(events)`:

```python
def _build_stage_aging(apps, stage_facts: dict) -> dict:
    """
    Returns per-stage aging pressure for admissions workflow management.

    The caller must pass apps and events already scoped to the current tenant.
    """
    now = timezone.now()

    sla_days = {
        "inquiry": 1,
        "tour_scheduled": 3,
        "tour_completed": 2,
        "application_started": 7,
        "application_submitted": 2,
        "in_review": 3,
        "accepted": 5,
        "waitlisted": 14,
        "declined": 0,
        "enrolled": 0,
    }

    buckets = {
        stage: {
            "count": 0,
            "max_days": 0,
            "total_days": 0,
            "avg_days": "0.00",
            "over_sla": 0,
            "sla_days": sla_days.get(stage, 0),
        }
        for stage in STAGES
    }

    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )

        anchor = app.updated_at or app.created_at
        age_days = max((now - anchor).days, 0)

        bucket = buckets[stage]
        bucket["count"] += 1
        bucket["max_days"] = max(bucket["max_days"], age_days)
        bucket["total_days"] += age_days

        if bucket["sla_days"] and age_days > bucket["sla_days"]:
            bucket["over_sla"] += 1

    for bucket in buckets.values():
        if bucket["count"]:
            bucket["avg_days"] = _d2(Decimal(bucket["total_days"]) / Decimal(bucket["count"]))
        bucket.pop("total_days", None)

    return buckets
```

Then inside `admissions_summary`, after:

```python
velocity = _build_velocity(events)
```

add:

```python
stage_aging = _build_stage_aging(apps, stage_facts)
```

Then add this field to the response payload:

```python
"stage_aging": stage_aging,
```

Expected return payload section:

```python
return Response(
    {
        "academic_year": ay_name,
        "date_from": request.query_params.get("date_from"),
        "date_to": request.query_params.get("date_to"),
        "pipeline": {"total": pipeline_total, "by_stage": stage_counts},
        "conversion": conversion,
        "velocity_days": velocity,
        "stage_aging": stage_aging,
        "top_sources": top_sources,
    }
)
```

## Backend test to add locally

Add to `backend/applications/tests/test_admissions_endpoints.py`, adapting the client fixture name to the existing file if needed:

```python
def test_admissions_summary_includes_stage_aging(authenticated_admissions_client, school):
    response = authenticated_admissions_client.get(
        "/api/v1/admissions/summary/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()

    assert "stage_aging" in payload
    assert "application_submitted" in payload["stage_aging"]

    submitted = payload["stage_aging"]["application_submitted"]
    assert "count" in submitted
    assert "max_days" in submitted
    assert "avg_days" in submitted
    assert "over_sla" in submitted
    assert "sla_days" in submitted
```

## Evidence to return in chat

Paste back:

1. `npm run verify:dashboard-completeness` final output.
2. `npm run test -- --run` final pass/fail summary.
3. `npm run build` final pass/fail summary.
4. `python -m pytest applications/tests/test_admissions_endpoints.py -q` final summary.
5. `audit-artifacts/evening-release-truth/<timestamp>/00_SUMMARY.md` contents.
6. Screenshot of Admissions dashboard showing the page-level data truth status and Stage Aging Pressure KPI.

## Merge rule

Do not merge until frontend test, build, backend admissions test, and evening proof runner are green or all failures are explicitly dispositioned in the PR.
