import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from core.management.commands import audit_tenant_relationship_integrity as audit_command
from core.models import School
from households.models import Guardian, Household


@pytest.mark.django_db
def test_audit_reports_cross_tenant_household_relationship():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    household = Household.objects.create(school_id=school_a.id, name="Family")
    Guardian.objects.create(
        school_id=school_b.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())

    guardian_audit = next(
        item
        for item in payload["relationships"]
        if item["model"] == "households.Guardian"
        and item["relation"] == "household"
    )

    assert payload["mode"] == "read_only"
    assert payload["production_authorization"] is False
    assert guardian_audit["row_count"] == 1
    assert guardian_audit["invalid_school_id_count"] == 0
    assert guardian_audit["parent_tenant_mismatch_count"] == 1
    assert payload["totals"]["mismatches"] >= 1
    assert payload["totals"]["unique_anomaly_rows"] == 1


@pytest.mark.django_db
def test_audit_fail_on_anomaly_is_nonzero_and_non_destructive():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")
    household = Household.objects.create(school_id=school_a.id, name="Family")
    guardian = Guardian.objects.create(
        school_id=school_b.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    with pytest.raises(CommandError, match="unique unexplained anomaly"):
        call_command(
            "audit_tenant_relationship_integrity",
            fail_on_anomaly=True,
            stdout=StringIO(),
        )

    guardian.refresh_from_db()
    assert guardian.school_id == school_b.id
    assert guardian.household_id == household.id


@pytest.mark.django_db
def test_audit_accepts_tenant_consistent_household_relationships():
    school = School.objects.create(name="School A")
    household = Household.objects.create(school_id=school.id, name="Family")
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )

    stdout = StringIO()
    call_command(
        "audit_tenant_relationship_integrity",
        fail_on_anomaly=True,
        stdout=stdout,
    )
    payload = json.loads(stdout.getvalue())

    assert payload["totals"]["mismatches"] == 0
    assert payload["totals"]["invalid_school_ids"] == 0
    assert payload["totals"]["unique_anomaly_rows"] == 0


def test_relationship_registry_covers_grade_entry_tenant_paths():
    grade_entry_paths = {
        (model, parent_path, relation)
        for model, parent_path, relation in audit_command.RELATIONSHIPS
        if model == "gradebook.GradeEntry"
    }

    assert grade_entry_paths == {
        ("gradebook.GradeEntry", "section__school_id", "section"),
        ("gradebook.GradeEntry", "student__school_id", "student"),
        ("gradebook.GradeEntry", "assignment__school_id", "assignment"),
    }


@pytest.mark.django_db
def test_overall_anomaly_rows_are_deduplicated_across_relationships(monkeypatch):
    school = School.objects.create(name="School A")
    household = Household.objects.create(school_id=school.id, name="Family")
    invalid_school_id = "00000000-0000-0000-0000-000000000099"
    Guardian.objects.create(
        school_id=invalid_school_id,
        household=household,
        first_name="Pat",
        last_name="Guardian",
    )
    monkeypatch.setattr(
        audit_command,
        "RELATIONSHIPS",
        (
            ("households.Guardian", "household__school_id", "household"),
            ("households.Guardian", "household__school_id", "household"),
        ),
    )

    stdout = StringIO()
    call_command("audit_tenant_relationship_integrity", stdout=stdout)
    payload = json.loads(stdout.getvalue())

    assert payload["totals"]["invalid_school_ids"] == 2
    assert payload["totals"]["mismatches"] == 2
    assert payload["totals"]["unique_invalid_school_rows"] == 1
    assert payload["totals"]["unique_mismatch_rows"] == 1
    assert payload["totals"]["unique_anomaly_rows"] == 1
