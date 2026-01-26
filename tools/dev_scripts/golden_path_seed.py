from __future__ import annotations

import json
import os
import sys
from datetime import date
from datetime import datetime
from decimal import Decimal

import django


def main() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backend_root = os.path.join(repo_root, "backend")
    sys.path.insert(0, backend_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    django.setup()

    from aid.models import AidApplication, AidAward
    from billing.models import BillingRun, Invoice
    from core.models import AcademicYear, Family, School, Student
    from finance.models import ChartAccount
    from households.models import Household
    from ledger.models import Charge, LedgerAccount

    school = School.objects.order_by("created_at", "id").first()
    if not school:
        raise RuntimeError("No School found; run dev_bootstrap")

    academic_year = (
        AcademicYear.objects.filter(school=school)
        .order_by("-is_current", "-start_date", "id")
        .first()
    )
    if not academic_year:
        academic_year = AcademicYear.objects.create(
            school=school,
            name="2026–2027",
            start_date=date(2026, 8, 15),
            end_date=date(2027, 6, 10),
            is_current=True,
        )

    family, _ = Family.objects.get_or_create(school=school, family_name="GP Family")
    student, _ = Student.objects.get_or_create(
        school=school,
        family=family,
        student_number="GP0001",
        defaults={"first_name": "Golden", "last_name": "Path", "dob": date(2010, 1, 1)},
    )

    ChartAccount.objects.get_or_create(
        school=school,
        code="AID",
        defaults={"name": "Financial Aid", "account_type": "INCOME", "is_active": True},
    )

    aid_app, _ = AidApplication.objects.get_or_create(
        school=school,
        academic_year=academic_year,
        family=family,
        defaults={"status": AidApplication.STATUS_NEEDS_INFO},
    )
    if aid_app.status != AidApplication.STATUS_NEEDS_INFO:
        aid_app.status = AidApplication.STATUS_NEEDS_INFO
        aid_app.save(update_fields=["status"])

    # Always create a fresh award so POST_ACCEPTED_AWARDS can demonstrate a real posting.
    # (Existing awards may already be posted, which would make the run a no-op.)
    aid_award = AidAward.objects.create(
        school=school,
        academic_year=academic_year,
        student=student,
        awarded_cents=25000,
        decision_status=AidAward.DECISION_ACCEPTED,
    )

    household, _ = Household.objects.get_or_create(school_id=school.id, name="GP Household")
    ledger_acct, _ = LedgerAccount.objects.get_or_create(school_id=school.id, household=household)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create a fresh charge + invoice each run so payment application is deterministic and doesn't depend on prior runs.
    charge = Charge.objects.create(
        school_id=school.id,
        account=ledger_acct,
        description=f"GP Tuition Charge {run_id}",
        amount=Decimal("250.00"),
    )

    billing_run, _ = BillingRun.objects.get_or_create(
        school_id=school.id,
        term=f"2026-GP-{run_id}",
        defaults={"run_type": "TUITION"},
    )

    invoice = Invoice.objects.create(
        school_id=school.id,
        billing_run=billing_run,
        household=household,
        due_on=date.today(),
        total_amount=Decimal("250.00"),
        ledger_charge_id=charge.id,
    )

    print(
        json.dumps(
            {
                "school_id": str(school.id),
                "school_name": school.name,
                "year_id": str(academic_year.id),
                "year_name": academic_year.name,
                "aid_application_id": str(aid_app.id),
                "aid_award_id": str(aid_award.id),
                "invoice_id": str(invoice.id),
                "household_id": str(household.id),
                "ledger_charge_id": str(charge.id),
            }
        )
    )


if __name__ == "__main__":
    main()
