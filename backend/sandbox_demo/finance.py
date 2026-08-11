from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from django.conf import settings
from django.db import transaction

from core.models import UserAccount, UserRole
from finance.models import (
    FinanceAllocation,
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
    PaymentStatus,
    Processor,
)
from finance.services import OverRefundError, initiate_refund, settle_payment_and_allocate
from households.models import Guardian as HouseholdGuardian, Household

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS

FINANCE_EMAIL = SANDBOX_PERSONAS["finance_director"].email
FINANCE_ROLE_CODE = SANDBOX_PERSONAS["finance_director"].role_code
PARENT_EMAIL = SANDBOX_PERSONAS["parent"].email
SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
DEMO_PAYMENT_KEY = "sandbox-finance-director-demo-payment-v1"
VOID_REFERENCE = "HCA-DEMO-VOIDED-FEE"


class SandboxFinanceError(Exception):
    pass


@dataclass(frozen=True)
class SandboxFinanceState:
    family_account: str
    obligation_id: int | None
    obligation_reference: str
    obligation_amount_cents: int
    allocated_cents: int
    remaining_cents: int
    authoritative_balance_cents: int
    open_obligation_count: int
    voided_obligation_count: int
    voided_amount_excluded_cents: int
    payment_id: int | None
    payment_status: str
    payment_history_count: int
    allocation_history_count: int
    reconciliation_status: str
    exception_control_status: str


def _require_finance_director(user) -> UserAccount:
    if not bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)):
        raise SandboxFinanceError("sandbox_open_session_required")
    if user is None or not getattr(user, "is_authenticated", False):
        raise SandboxFinanceError("authenticated_finance_director_required")
    if str(getattr(user, "school_id", "") or "") != str(SCHOOL_ID):
        raise SandboxFinanceError("heritage_school_required")
    if str(getattr(user, "email", "") or "").strip().lower() != FINANCE_EMAIL:
        raise SandboxFinanceError("heritage_finance_director_required")
    if not UserRole.objects.filter(user=user, school_id=SCHOOL_ID, role_code=FINANCE_ROLE_CODE).exists():
        raise SandboxFinanceError("finance_director_role_required")
    return user


def _parent_user() -> UserAccount:
    try:
        return UserAccount.objects.get(school_id=SCHOOL_ID, username=PARENT_EMAIL)
    except UserAccount.DoesNotExist as exc:
        raise SandboxFinanceError("heritage_parent_not_seeded") from exc


def _ensure_ledger_identity(parent: UserAccount) -> None:
    household, _ = Household.objects.update_or_create(
        school_id=SCHOOL_ID,
        name="Reed Family",
        defaults={"address1": "100 Demo Lane", "city": "Fairview", "state": "PA", "postal_code": "19000", "is_active": True},
    )
    HouseholdGuardian.objects.update_or_create(
        school_id=SCHOOL_ID,
        household=household,
        email=parent.email,
        defaults={"first_name": parent.first_name or "Miriam", "last_name": parent.last_name or "Reed", "phone": "555-0100", "is_primary": True},
    )


def _ensure_voided_obligation(parent: UserAccount, director: UserAccount | None = None) -> FinanceObligation:
    obligation, _ = FinanceObligation.objects.update_or_create(
        school_id=SCHOOL_ID,
        payer_user=parent,
        reference=VOID_REFERENCE,
        defaults={
            "obligation_type": ObligationType.FEE,
            "status": MoneyStatus.VOID,
            "description": "Voided sandbox activity fee",
            "due_date": date(2026, 9, 1),
            "amount_cents": 12500,
            "currency": "USD",
            "academic_year_label": "2026-2027",
            "created_by": director,
            "updated_by": director,
        },
    )
    return obligation


def seed_heritage_finance_context() -> dict[str, str]:
    parent = _parent_user()
    director = UserAccount.objects.filter(school_id=SCHOOL_ID, username=FINANCE_EMAIL).first()
    _ensure_ledger_identity(parent)
    voided = _ensure_voided_obligation(parent, director)
    return {"finance_void_control_id": str(voided.id)}


def _target_obligation(parent: UserAccount) -> FinanceObligation:
    obligation = FinanceObligation.objects.filter(
        school_id=SCHOOL_ID,
        payer_user=parent,
        reference="HCA-DEMO-TUITION-01",
    ).order_by("id").first()
    if obligation is None:
        raise SandboxFinanceError("demo_obligation_not_seeded")
    return obligation


def _authoritative_balance(parent: UserAccount) -> tuple[int, int, int, int]:
    obligations = list(FinanceObligation.objects.filter(school_id=SCHOOL_ID, payer_user=parent))
    non_void = [row for row in obligations if row.status != MoneyStatus.VOID]
    void_rows = [row for row in obligations if row.status == MoneyStatus.VOID]
    total_due = sum(int(row.amount_cents) for row in non_void)
    allocated = sum(int(value) for value in FinanceAllocation.objects.filter(school_id=SCHOOL_ID, obligation__in=non_void).values_list("amount_cents", flat=True))
    return max(total_due - allocated, 0), len(non_void), len(void_rows), sum(int(row.amount_cents) for row in void_rows)


def serialize_finance_state(user) -> SandboxFinanceState:
    _require_finance_director(user)
    parent = _parent_user()
    obligation = _target_obligation(parent)
    payment = FinancePayment.objects.filter(school_id=SCHOOL_ID, idempotency_key=DEMO_PAYMENT_KEY).order_by("-created_at").first()
    allocated = int(sum(FinanceAllocation.objects.filter(school_id=SCHOOL_ID, obligation=obligation).values_list("amount_cents", flat=True)))
    remaining = max(int(obligation.amount_cents) - allocated, 0)
    authoritative_balance, open_count, void_count, void_amount = _authoritative_balance(parent)
    reconciled = bool(payment and payment.status == PaymentStatus.SETTLED and allocated >= int(obligation.amount_cents) and remaining == 0)
    return SandboxFinanceState(
        family_account="Reed Family",
        obligation_id=obligation.id,
        obligation_reference=obligation.reference,
        obligation_amount_cents=int(obligation.amount_cents),
        allocated_cents=allocated,
        remaining_cents=remaining,
        authoritative_balance_cents=authoritative_balance,
        open_obligation_count=open_count,
        voided_obligation_count=void_count,
        voided_amount_excluded_cents=void_amount,
        payment_id=payment.id if payment else None,
        payment_status=str(payment.status) if payment else "not_started",
        payment_history_count=FinancePayment.objects.filter(school_id=SCHOOL_ID, payer_user=parent).count(),
        allocation_history_count=FinanceAllocation.objects.filter(school_id=SCHOOL_ID, payment__payer_user=parent).count(),
        reconciliation_status="reconciled" if reconciled else "open",
        exception_control_status="verified" if reconciled else "pending",
    )


@transaction.atomic
def apply_demo_payment(user) -> dict:
    director = _require_finance_director(user)
    parent = _parent_user()
    _ensure_ledger_identity(parent)
    _ensure_voided_obligation(parent, director)
    obligation = _target_obligation(parent)
    payment, _ = FinancePayment.objects.get_or_create(
        school_id=SCHOOL_ID,
        idempotency_key=DEMO_PAYMENT_KEY,
        defaults={"payer_user": parent, "amount_cents": int(obligation.amount_cents), "currency": "USD", "processor": Processor.MANUAL, "status": PaymentStatus.PENDING, "created_by": director},
    )
    if payment.status != PaymentStatus.SETTLED:
        payment = settle_payment_and_allocate(payment=payment, allocations_payload=[{"obligation_id": obligation.id, "amount_cents": int(obligation.amount_cents)}])
    try:
        initiate_refund(payment=payment, amount_cents=int(payment.amount_cents) + 1, processor=Processor.MANUAL, created_by=director, idempotency_key="sandbox-over-refund-must-fail")
    except OverRefundError:
        pass
    else:
        raise SandboxFinanceError("over_refund_control_failed")
    state = serialize_finance_state(director)
    if state.reconciliation_status != "reconciled":
        raise SandboxFinanceError("reconciliation_failed")
    if state.voided_obligation_count < 1 or state.voided_amount_excluded_cents < 1:
        raise SandboxFinanceError("void_integrity_failed")
    payload = asdict(state)
    payload.update({"over_refund_blocked": True, "voided_charges_excluded_from_balance": True, "external_payment_processed": False})
    return payload
