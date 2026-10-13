"""Offline, reviewed-input calculation foundation. No routes or source writes.

DTOs are trusted adapter output, never request payloads. Evidence references are
assertions to validate structurally; this module cannot certify their contents.
See docs/accounting/CASH_FORECAST_SOURCE_CONTRACT.md before constructing them.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Context, Decimal, localcontext
from uuid import UUID

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
SOURCE_MODELS = {
    "tuition": "billing.InstallmentScheduleItem",
    "vendor": "apps.accounting.PayableBill",
    "payroll": "approved_school_payroll_occurrence",
    "recurring": "approved_school_recurring_occurrence",
}
KINDS = frozenset(SOURCE_MODELS)


@dataclass(frozen=True)
class Evidence:
    school_id: UUID
    currency: str
    reference: str
    as_of: date
    verified_on: date
    reviewer: str


@dataclass(frozen=True)
class OpeningCash:
    evidence: Evidence
    bank_cash: Decimal
    restricted: Decimal
    board_designated: Decimal
    holds: Decimal
    available: Decimal
    reconciliation_reference: str


@dataclass(frozen=True)
class Coverage:
    kind: str
    evidence: Evidence
    start: date
    end: date  # exclusive
    count: int
    total: Decimal


@dataclass(frozen=True)
class Receivable:
    evidence: Evidence
    invoice_id: str
    charge_id: str
    outstanding: Decimal  # after reconciled cash allocations and noncash credits


@dataclass(frozen=True)
class Commitment:
    evidence: Evidence
    kind: str
    source_id: str  # installment, bill, or approved commitment occurrence
    obligation_id: str  # ledger charge for tuition; bill/occurrence otherwise
    due_on: date
    amount: Decimal
    restriction: str = "UNRESTRICTED"
    state: str = "approved"
    source_model: str = ""


@dataclass(frozen=True)
class SettledPayment:
    evidence: Evidence
    payment_id: str
    provider_identity: str  # provider + payment ID, or reviewed manual receipt ID
    settled_on: date
    amount: Decimal
    refunded: Decimal  # settled refunds only; pending refund must block adapter
    state: str = "settled"


@dataclass(frozen=True)
class Snapshot:
    school_id: UUID
    currency: str
    start: date
    evaluated_on: date
    opening: OpeningCash | None
    coverage: tuple[Coverage, ...]
    receivables: tuple[Receivable, ...]
    commitments: tuple[Commitment, ...]
    payments: tuple[SettledPayment, ...]
    settlement_evidence: Evidence | None
    settlement_count: int
    settlement_net: Decimal


@dataclass(frozen=True)
class Week:
    start: date
    end: date  # exclusive
    opening: Decimal
    collections: Decimal
    disbursements: Decimal
    closing: Decimal
    source_references: tuple[str, ...]


@dataclass(frozen=True)
class Calculation:
    status: str
    reasons: tuple[str, ...]
    weeks: tuple[Week, ...] = ()
    flags: tuple[str, ...] = ("REVIEWED_ASSUMPTIONS", "COLLECTION_TIMING_UNCERTAIN", "OFFLINE_ONLY")


def _money(value):
    # Reject binary floats, NaN/infinity, sub-cent facts and excessive magnitudes.
    return (isinstance(value, Decimal) and value.is_finite()
            and abs(value) < Decimal("1000000000000")
            and value == value.quantize(CENT))


def _day(value):
    return type(value) is date


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def calculate_reviewed_cash(*, user, school, snapshot: Snapshot) -> Calculation:
    """Authorize first, validate all input, then calculate synthetic/reviewed weeks.

    NOT_READY has no weeks or partial cash totals. Even INPUTS_VALIDATED is not
    production authorization or independent verification of source documents.
    """
    from core.models import School
    from core.permissions import user_has_permission

    school = School.objects.filter(pk=getattr(school, "pk", None), is_active=True).first()
    if (school is None
            or not user_has_permission(user, "finance.view", school=school)):
        raise PermissionError("School finance permission required.")
    if not isinstance(snapshot, Snapshot) or snapshot.school_id != school.pk:
        raise PermissionError("School financial source mismatch.")
    return _calculate(snapshot)


def _calculate(s):
    # Caller Decimal context must not change financial arithmetic.
    with localcontext(Context(prec=40)):
        return _validate_and_roll_forward(s)


def _validate_and_roll_forward(s):
    errors = set()
    if (not isinstance(s.school_id, UUID) or s.currency != "USD"
            or not _day(s.start) or not _day(s.evaluated_on)):
        return Calculation("NOT_READY", ("INVALID_SCOPE_OR_CUTOFF",))
    cutoff = s.start - timedelta(days=1)
    end = s.start + timedelta(days=91)
    if not cutoff <= s.evaluated_on <= cutoff + timedelta(days=7):
        errors.add("STALE_SNAPSHOT")

    def evidence(e):
        if not isinstance(e, Evidence):
            errors.add("MISSING_EVIDENCE")
            return
        if e.school_id != s.school_id:
            errors.add("CROSS_TENANT_SOURCE")
        if e.currency != s.currency:
            errors.add("CURRENCY_MISMATCH")
        if (not _text(e.reference) or not _text(e.reviewer)
                or not _day(e.as_of) or not _day(e.verified_on)
                or e.as_of != cutoff
                or not cutoff <= e.verified_on <= s.evaluated_on):
            errors.add("UNVERIFIED_OR_STALE_EVIDENCE")

    o = s.opening
    if not isinstance(o, OpeningCash):
        errors.add("MISSING_OPENING_RECONCILIATION")
    else:
        evidence(o.evidence)
        amounts = (o.bank_cash, o.restricted, o.board_designated, o.holds, o.available)
        if not all(_money(x) and x >= ZERO for x in amounts):
            errors.add("INVALID_OPENING_AMOUNTS")
        elif o.available != o.bank_cash - o.restricted - o.board_designated - o.holds:
            errors.add("OPENING_RESTRICTION_MISMATCH")
        if not _text(o.reconciliation_reference):
            errors.add("MISSING_OPENING_RECONCILIATION")

    coverage = {}
    for c in s.coverage:
        evidence(c.evidence)
        if c.kind not in KINDS or c.kind in coverage:
            errors.add("INVALID_OR_DUPLICATE_COVERAGE")
        coverage[c.kind] = c
        if (c.start != s.start or c.end != end or type(c.count) is not int
                or c.count < 0 or not _money(c.total) or c.total < ZERO):
            errors.add("INCOMPLETE_COVERAGE")
    if set(coverage) != KINDS:
        errors.add("MISSING_COMMITMENT_COVERAGE")

    receivables = {}
    invoices = set()
    for r in s.receivables:
        evidence(r.evidence)
        if (not _text(r.invoice_id) or not _text(r.charge_id)
                or r.invoice_id in invoices or r.charge_id in receivables):
            errors.add("DUPLICATE_OR_UNLINKED_RECEIVABLE")
        invoices.add(r.invoice_id)
        receivables[r.charge_id] = r
        if not _money(r.outstanding) or r.outstanding < ZERO:
            errors.add("INVALID_RECEIVABLE")

    totals = {k: ZERO for k in KINDS}
    counts = {k: 0 for k in KINDS}
    scheduled = {}
    identities = set()
    obligations = set()
    for c in s.commitments:
        evidence(c.evidence)
        if c.kind not in KINDS:
            errors.add("NONCANONICAL_CASH_SOURCE")
            continue
        if c.source_model != SOURCE_MODELS[c.kind]:
            errors.add("NONCANONICAL_CASH_SOURCE")
        if c.restriction != "UNRESTRICTED":
            errors.add("RESTRICTED_COMMITMENT")
        if c.state != "approved":
            errors.add("UNAPPROVED_OR_PAID_COMMITMENT")
        if not _day(c.due_on) or not s.start <= c.due_on < end:
            errors.add("UNDATED_OR_OUT_OF_HORIZON_COMMITMENT")
        if not _money(c.amount) or c.amount <= ZERO:
            errors.add("INVALID_COMMITMENT_AMOUNT")
            continue
        if not _text(c.source_id) or not _text(c.obligation_id):
            errors.add("MISSING_CANONICAL_IDENTITY")
        identity = (c.kind, c.source_id)
        if identity in identities:
            errors.add("DUPLICATE_CASH_EVENT")
        identities.add(identity)
        if c.kind != "tuition":
            # Payroll represented in recurring, or a vendor bill represented as
            # recurring, must share its owning obligation ID and fail closed.
            if c.obligation_id in obligations:
                errors.add("DUPLICATE_OUTFLOW_OBLIGATION")
            obligations.add(c.obligation_id)
        else:
            scheduled[c.obligation_id] = scheduled.get(c.obligation_id, ZERO) + c.amount
            if c.obligation_id not in receivables:
                errors.add("UNLINKED_TUITION_COLLECTION")
        counts[c.kind] += 1
        totals[c.kind] += c.amount
    for charge, amount in scheduled.items():
        r = receivables.get(charge)
        if r and _money(r.outstanding) and amount > r.outstanding:
            errors.add("COLLECTION_EXCEEDS_NET_RECEIVABLE")
    for kind, c in coverage.items():
        if kind in KINDS and (c.count != counts[kind] or c.total != totals[kind]):
            errors.add("COVERAGE_RECONCILIATION_MISMATCH")

    # Settlement history is reconciliation evidence, never a future inflow.
    evidence(s.settlement_evidence)
    payment_ids = set()
    provider_ids = set()
    net = ZERO
    for p in s.payments:
        evidence(p.evidence)
        if (not _text(p.payment_id) or not _text(p.provider_identity)
                or p.payment_id in payment_ids or p.provider_identity in provider_ids):
            errors.add("DUPLICATE_OR_UNIDENTIFIED_SETTLEMENT")
        payment_ids.add(p.payment_id)
        provider_ids.add(p.provider_identity)
        if not _day(p.settled_on) or p.settled_on > cutoff:
            errors.add("UNSETTLED_OR_AFTER_CUTOFF_PAYMENT")
        if p.state not in {"settled", "partially_refunded", "refunded"}:
            errors.add("UNSETTLED_OR_REVERSED_PAYMENT")
        if (not _money(p.amount) or not _money(p.refunded)
                or p.amount <= ZERO or not ZERO <= p.refunded <= p.amount):
            errors.add("INVALID_SETTLEMENT_AMOUNT")
            continue
        if ((p.state == "settled" and p.refunded != ZERO)
                or (p.state == "refunded" and p.refunded != p.amount)
                or (p.state == "partially_refunded" and not ZERO < p.refunded < p.amount)):
            errors.add("REFUND_STATE_MISMATCH")
        net += p.amount - p.refunded
    if (type(s.settlement_count) is not int or s.settlement_count != len(s.payments)
            or not _money(s.settlement_net) or s.settlement_net != net):
        errors.add("SETTLEMENT_RECONCILIATION_MISMATCH")
    if errors:
        return Calculation("NOT_READY", tuple(sorted(errors)))

    weeks = []
    balance = o.available
    for index in range(13):
        start = s.start + timedelta(days=index * 7)
        stop = start + timedelta(days=7)
        events = [c for c in s.commitments if start <= c.due_on < stop]
        incoming = sum((c.amount for c in events if c.kind == "tuition"), ZERO)
        outgoing = sum((c.amount for c in events if c.kind != "tuition"), ZERO)
        closing = balance + incoming - outgoing
        weeks.append(Week(start, stop, balance, incoming, outgoing, closing,
                          tuple(sorted({c.evidence.reference for c in events}))))
        balance = closing
    flags = ("REVIEWED_ASSUMPTIONS", "COLLECTION_TIMING_UNCERTAIN", "OFFLINE_ONLY")
    if any(w.closing < ZERO for w in weeks):
        flags += ("NEGATIVE_AVAILABLE_CASH",)
    return Calculation("INPUTS_VALIDATED", (), tuple(weeks), flags)
