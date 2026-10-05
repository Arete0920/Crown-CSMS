from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch

from academics.models import Enrollment, Section
from households.models import Student
from ledger.models import LedgerAccount, Charge

from .models import BillingRun, Invoice, InvoiceLine, InstallmentPlan, InstallmentScheduleItem
from .payer_services import generate_payer_shares_for_invoice


@dataclass(frozen=True)
class RunResult:
    billing_run_id: UUID
    invoices_created: int
    students_billed: int
    total_amount: Decimal


def _student_household_id(student: Student):
    return getattr(student, "household_id", None)


def _split_amount_evenly(total: Decimal, parts: int) -> list[Decimal]:
    if parts <= 0:
        raise ValueError("parts must be > 0")

    total = Decimal(str(total))
    if parts == 1:
        return [total]

    # Truncate per-part amount to cents; remainder goes to the last part
    from decimal import ROUND_DOWN

    base = (total / Decimal(str(parts))).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    amounts = [base for _ in range(parts - 1)]
    last = total - (base * Decimal(str(parts - 1)))
    last = last.quantize(Decimal("0.01"))
    amounts.append(last)
    return amounts


@transaction.atomic
def generate_installments_for_household(
    *,
    school_id,
    household_id,
    term: str,
    plan: InstallmentPlan,
    amount: Decimal,
) -> list[InstallmentScheduleItem]:
    """Generate per-household installment schedule items (idempotent)."""
    if plan.school_id != school_id:
        raise ValueError("school_id mismatch")
    if (plan.term or "").strip() != (term or "").strip():
        raise ValueError("term mismatch")

    existing = InstallmentScheduleItem.objects.filter(
        school_id=school_id,
        plan=plan,
        household_id=household_id,
    ).order_by("sequence")
    if existing.exists():
        return list(existing)

    n = int(getattr(plan, "installment_count", 1) or 1)
    if n <= 0:
        raise ValueError("installment_count must be > 0")

    amounts = _split_amount_evenly(Decimal(str(amount)), n)
    first_due_on = getattr(plan, "first_due_on", None)
    if not first_due_on:
        raise ValueError("first_due_on is required")

    cadence_days = int(getattr(plan, "cadence_days", 30) or 30)
    if cadence_days <= 0:
        raise ValueError("cadence_days must be > 0")

    items: list[InstallmentScheduleItem] = []
    for i, amt in enumerate(amounts, start=1):
        due_on = first_due_on + timedelta(days=cadence_days * (i - 1))
        item = InstallmentScheduleItem.objects.create(
            school_id=school_id,
            plan=plan,
            household_id=household_id,
            sequence=i,
            due_on=due_on,
            amount=amt,
        )
        items.append(item)

    return items


@transaction.atomic
def create_tuition_billing_run(
    *,
    school_id,
    term: str,
    amount_per_student: Decimal,
    description: str = "Tuition Billing Run",
    installment_plan_id: UUID | None = None,
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

    plan: InstallmentPlan | None = None
    if installment_plan_id:
        plan = InstallmentPlan.objects.get(pk=installment_plan_id, school_id=school_id)

    for household_id, st_list in by_household.items():
        household_total = amount_per_student * Decimal(str(len(st_list)))

        if not plan:
            inv = Invoice.objects.create(
                school_id=school_id,
                billing_run=run,
                household_id=household_id,
                total_amount=household_total,
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

            generate_payer_shares_for_invoice(inv)

            acct, _ = LedgerAccount.objects.get_or_create(school_id=school_id, household_id=household_id)
            ch = Charge.objects.create(
                school_id=school_id,
                account=acct,
                description=f"Tuition - {term}",
                amount=household_total,
            )
            inv.ledger_charge_id = ch.id
            inv.save(update_fields=["ledger_charge_id", "updated_at"])

            total_amount += household_total
            continue

        # Installment plan path: N invoices per household, one per schedule item
        items = generate_installments_for_household(
            school_id=school_id,
            household_id=household_id,
            term=term,
            plan=plan,
            amount=household_total,
        )

        for item in items:
            inv = Invoice.objects.create(
                school_id=school_id,
                billing_run=run,
                household_id=household_id,
                total_amount=Decimal(str(item.amount)),
                due_on=item.due_on,
            )
            invoices_created += 1

            # Distribute the installment amount across students for line items.
            per_student_amounts = _split_amount_evenly(Decimal(str(item.amount)), len(st_list))
            for st, line_amt in zip(st_list, per_student_amounts, strict=False):
                InvoiceLine.objects.create(
                    school_id=school_id,
                    invoice=inv,
                    student=st,
                    description=f"Tuition Installment {item.sequence}/{plan.installment_count} - {term}",
                    amount=line_amt,
                )
                students_billed += 1

            generate_payer_shares_for_invoice(inv)

            acct, _ = LedgerAccount.objects.get_or_create(school_id=school_id, household_id=household_id)
            ch = Charge.objects.create(
                school_id=school_id,
                account=acct,
                description=f"Tuition Installment {item.sequence}/{plan.installment_count} - {term}",
                amount=Decimal(str(item.amount)),
            )
            inv.ledger_charge_id = ch.id
            inv.save(update_fields=["ledger_charge_id", "updated_at"])

            item.invoice = inv
            item.save(update_fields=["invoice", "updated_at"])

            total_amount += Decimal(str(item.amount))

    return RunResult(
        billing_run_id=run.id,
        invoices_created=invoices_created,
        students_billed=students_billed,
        total_amount=total_amount,
    )
