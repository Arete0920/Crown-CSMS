from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch

from academics.models import Enrollment, Section
from households.models import Student
from ledger.models import LedgerAccount, Charge

from .models import BillingRun, Invoice, InvoiceLine


@dataclass(frozen=True)
class RunResult:
    billing_run_id: UUID
    invoices_created: int
    students_billed: int
    total_amount: Decimal


def _student_household_id(student: Student):
    return getattr(student, "household_id", None)


@transaction.atomic
def create_tuition_billing_run(
    *,
    school_id,
    term: str,
    amount_per_student: Decimal,
    description: str = "Tuition Billing Run",
):
    """
    Spine logic:
    - Find all enrollments for Sections in `term`
    - Unique students
    - Group by household
    - Create BillingRun
    - Create Invoice per household
    - Create InvoiceLine per student
    - Ensure LedgerAccount, create ONE Charge per household for invoice total
    """
    term = (term or "").strip()
    if not term:
        raise ValueError("term is required")
    if amount_per_student is None:
        raise ValueError("amount_per_student is required")

    run = BillingRun.objects.create(
        school_id=school_id,
        term=term[:24],
        run_type="TUITION",
        description=(description or "Tuition Billing Run")[:200],
        amount_per_student=amount_per_student,
    )

    sections = Section.objects.filter(school_id=school_id, term=term)
    enrollments = (
        Enrollment.objects.select_related("student", "section")
        .filter(school_id=school_id, section__in=sections)
    )

    # Unique students billed
    students = []
    seen = set()
    for e in enrollments:
        sid = e.student_id
        if sid in seen:
            continue
        seen.add(sid)
        students.append(e.student)

    # Group by household
    by_household = {}
    for st in students:
        hid = _student_household_id(st)
        if not hid:
            continue
        by_household.setdefault(hid, []).append(st)

    invoices_created = 0
    students_billed = 0
    total_amount = Decimal("0.00")

    for household_id, st_list in by_household.items():
        invoice_total = amount_per_student * Decimal(str(len(st_list)))
        inv = Invoice.objects.create(
            school_id=school_id,
            billing_run=run,
            household_id=household_id,
            total_amount=invoice_total,
        )
        invoices_created += 1

        for st in st_list:
            InvoiceLine.objects.create(
                school_id=school_id,
                invoice=inv,
                student=st,
                description=f"Tuition - {term}",
                amount=amount_per_student,
            )
            students_billed += 1

        acct, _ = LedgerAccount.objects.get_or_create(school_id=school_id, household_id=household_id)
        ch = Charge.objects.create(
            school_id=school_id,
            account=acct,
            description=f"Tuition - {term}",
            amount=invoice_total,
        )
        inv.ledger_charge_id = ch.id
        inv.save(update_fields=["ledger_charge_id", "updated_at"])

        total_amount += invoice_total

    return RunResult(
        billing_run_id=run.id,
        invoices_created=invoices_created,
        students_billed=students_billed,
        total_amount=total_amount,
    )
