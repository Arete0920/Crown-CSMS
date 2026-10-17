"""Regression checks for read-only service-ledger inventory."""
import json
from decimal import Decimal
from io import StringIO
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.models import School
from outreach.models import ServiceLog, STATUS_APPROVED


@pytest.mark.django_db
def test_service_reconciliation_reports_independent_ledger_totals():
    school = School.objects.create(name="Reconciliation School")
    log = ServiceLog.objects.create(
        school_id=school.pk, participant_type="STAFF",
        status=STATUS_APPROVED, hours="2.50",
    )
    output = StringIO()
    call_command("reconcile_service_ledgers", school_id=str(school.pk), stdout=output)
    report = json.loads(output.getvalue())
    row = report["schools"][0]
    assert report["mode"] == "read_only"
    assert report["candidate_matching"] == "disabled"
    assert row["service_entries"] == 0
    assert row["outreach_logs"] == 1
    assert Decimal(row["outreach_approved_hours_separate_not_credit"]) == Decimal("2.50")
    assert row["outreach_approved_nonstudent_or_unassigned_logs"] == 1
    log.refresh_from_db()
    assert log.status == STATUS_APPROVED


@pytest.mark.django_db
def test_service_reconciliation_school_filter_and_unknown_school():
    first = School.objects.create(name="Reconciliation First")
    School.objects.create(name="Reconciliation Second")
    output = StringIO()
    call_command("reconcile_service_ledgers", school_id=str(first.pk), stdout=output)
    assert [row["school_id"] for row in json.loads(output.getvalue())["schools"]] == [str(first.pk)]
    with pytest.raises(CommandError, match="Unknown school id"):
        call_command("reconcile_service_ledgers", school_id="00000000-0000-0000-0000-000000000000")
