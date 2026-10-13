from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, localcontext
from uuid import uuid4

import pytest

from apps.accounting.cash_forecast import (
    Commitment, Coverage, Evidence, OpeningCash, Receivable, SettledPayment,
    Snapshot, SOURCE_MODELS, calculate_reviewed_cash,
)
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db
D = Decimal
START = date(2026, 10, 14)
CUTOFF = START - timedelta(days=1)


@pytest.fixture
def finance():
    school = School.objects.create(name="Synthetic School")
    user = UserAccount.objects.create_user(username="cash-finance", email="cash-finance@example.test", school=school)
    permission, _ = CrownPermission.objects.get_or_create(code="finance.view", defaults={"description": "Finance"})
    RolePermission.objects.get_or_create(role_code="cash_test_finance", permission=permission)
    UserRole.objects.create(user=user, school=school, role_code="cash_test_finance")
    return user, school


def sample(school):
    e = Evidence(school.pk, "USD", "synthetic-reviewed-record", CUTOFF, CUTOFF, "synthetic-finance-reviewer")
    opening = OpeningCash(e, D("1000.00"), D("200.00"), D("100.00"), D("50.00"), D("650.00"), "synthetic-bank-reconciliation")
    events = (
        Commitment(e, "tuition", "installment-1", "charge-1", START, D("300.00")),
        Commitment(e, "vendor", "bill-1", "vendor:bill-1", START + timedelta(days=6), D("100.00")),
        Commitment(e, "payroll", "payrun-1", "payroll:payrun-1", START + timedelta(days=7), D("500.00")),
        Commitment(e, "recurring", "rent-1", "recurring:rent-1", START + timedelta(days=90), D("100.00")),
    )
    events = tuple(replace(c, source_model=SOURCE_MODELS[c.kind]) for c in events)
    coverage = tuple(Coverage(k, e, START, START + timedelta(days=91), 1, a)
                     for k, a in (("tuition", D("300.00")), ("vendor", D("100.00")),
                                  ("payroll", D("500.00")), ("recurring", D("100.00"))))
    payment = SettledPayment(e, "canonical-payment-1", "provider:payment-1", CUTOFF, D("250.00"), D("50.00"), "partially_refunded")
    return Snapshot(school.pk, "USD", START, CUTOFF, opening, coverage,
                    (Receivable(e, "invoice-1", "charge-1", D("300.00")),),
                    events, (payment,), e, 1, D("200.00"))


def run(finance, s):
    user, school = finance
    return calculate_reviewed_cash(user=user, school=school, snapshot=s)


def blocked(finance, s, reason):
    result = run(finance, s)
    assert result.status == "NOT_READY"
    assert reason in result.reasons
    assert result.weeks == ()


def test_decimal_roll_forward_and_settlement_not_readded(finance):
    s = sample(finance[1])
    result = run(finance, s)
    assert result.status == "INPUTS_VALIDATED"
    assert len(result.weeks) == 13
    assert result.weeks[0].opening == D("650.00")
    assert result.weeks[0].closing == D("850.00")
    assert result.weeks[1].closing == D("350.00")
    assert result.weeks[-1].closing == D("250.00")
    assert result.weeks[-1].end == START + timedelta(days=91)
    for i, w in enumerate(result.weeks):
        assert w.closing == w.opening + w.collections - w.disbursements
        assert w.end - w.start == timedelta(days=7)
        if i:
            assert w.opening == result.weeks[i - 1].closing
    assert sum((w.collections for w in result.weeks), D("0.00")) == D("300.00")
    assert "OFFLINE_ONLY" in result.flags
    assert result.weeks[0].source_references


@pytest.mark.parametrize("role", ["teacher", "board", "superuser", "other-school", "inactive-user", "anonymous"])
def test_unauthorized_access_rejected_before_snapshot_validation(finance, role):
    _, school = finance
    user = UserAccount.objects.create_user(username=role, email=f"{role}@example.test", school=school)
    if role == "superuser":
        user.is_superuser = True
        user.save()
    if role == "inactive-user":
        user.is_active = False
        user.save()
    if role == "anonymous":
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
    elif role == "other-school":
        other = School.objects.create(name="Other School")
        UserRole.objects.create(user=user, school=other, role_code="cash_test_finance")
    else:
        UserRole.objects.create(user=user, school=school, role_code=role)
    with pytest.raises(PermissionError):
        calculate_reviewed_cash(user=user, school=school, snapshot=None)


def test_inactive_or_missing_school_denied(finance):
    user, school = finance
    school.is_active = False
    school.save()
    # Stale caller object must not override persisted inactive-school status.
    school.is_active = True
    for target in (school, None):
        with pytest.raises(PermissionError):
            calculate_reviewed_cash(user=user, school=target, snapshot=sample(school))


def test_cross_tenant_snapshot_denied(finance):
    with pytest.raises(PermissionError):
        run(finance, replace(sample(finance[1]), school_id=uuid4()))


@pytest.mark.parametrize("source", ["opening", "coverage", "receivable", "commitment", "payment", "settlement"])
def test_cross_tenant_nested_evidence_rejected(finance, source):
    s = sample(finance[1])
    foreign = replace(s.opening.evidence, school_id=uuid4())
    changes = {
        "opening": {"opening": replace(s.opening, evidence=foreign)},
        "coverage": {"coverage": (replace(s.coverage[0], evidence=foreign),) + s.coverage[1:]},
        "receivable": {"receivables": (replace(s.receivables[0], evidence=foreign),)},
        "commitment": {"commitments": (replace(s.commitments[0], evidence=foreign),) + s.commitments[1:]},
        "payment": {"payments": (replace(s.payments[0], evidence=foreign),)},
        "settlement": {"settlement_evidence": foreign},
    }
    blocked(finance, replace(s, **changes[source]), "CROSS_TENANT_SOURCE")


@pytest.mark.parametrize("opening,reason", [
    (None, "MISSING_OPENING_RECONCILIATION"),
    ({"available": D("1000.00")}, "OPENING_RESTRICTION_MISMATCH"),
    ({"reconciliation_reference": ""}, "MISSING_OPENING_RECONCILIATION"),
    ({"restricted": None}, "INVALID_OPENING_AMOUNTS"),
    ({"available": 650.0}, "INVALID_OPENING_AMOUNTS"),
    ({"holds": D("0.001")}, "INVALID_OPENING_AMOUNTS"),
    ({"available": D("NaN")}, "INVALID_OPENING_AMOUNTS"),
    ({"bank_cash": D("Infinity")}, "INVALID_OPENING_AMOUNTS"),
])
def test_opening_cash_failures(finance, opening, reason):
    s = sample(finance[1])
    blocked(finance, replace(s, opening=None if opening is None else replace(s.opening, **opening)), reason)


@pytest.mark.parametrize("changes", [
    {"reference": ""}, {"reviewer": ""}, {"as_of": CUTOFF - timedelta(days=1)},
    {"verified_on": CUTOFF - timedelta(days=1)}, {"verified_on": START},
])
def test_unreviewed_or_stale_evidence(finance, changes):
    s = sample(finance[1])
    blocked(finance, replace(s, opening=replace(s.opening, evidence=replace(s.opening.evidence, **changes))), "UNVERIFIED_OR_STALE_EVIDENCE")


def test_stale_snapshot_and_mixed_currency(finance):
    s = sample(finance[1])
    blocked(finance, replace(s, evaluated_on=CUTOFF + timedelta(days=8)), "STALE_SNAPSHOT")
    blocked(finance, replace(s, opening=replace(s.opening, evidence=replace(s.opening.evidence, currency="EUR"))), "CURRENCY_MISMATCH")
    blocked(finance, replace(s, currency=""), "INVALID_SCOPE_OR_CUTOFF")


@pytest.mark.parametrize("kind", ["payroll", "recurring", "tuition", "vendor"])
def test_missing_coverage_is_not_zero(finance, kind):
    s = sample(finance[1])
    blocked(finance, replace(s, coverage=tuple(c for c in s.coverage if c.kind != kind)), "MISSING_COMMITMENT_COVERAGE")


def test_incomplete_payroll_and_coverage_totals(finance):
    s = sample(finance[1])
    payroll = replace(s.coverage[2], end=START + timedelta(days=30))
    blocked(finance, replace(s, coverage=s.coverage[:2] + (payroll,) + s.coverage[3:]), "INCOMPLETE_COVERAGE")
    blocked(finance, replace(s, commitments=s.commitments[:2] + s.commitments[3:]), "COVERAGE_RECONCILIATION_MISMATCH")
    blocked(finance, replace(s, coverage=s.coverage + (s.coverage[0],)), "INVALID_OR_DUPLICATE_COVERAGE")


def test_explicit_reviewed_zero_coverage(finance):
    s = sample(finance[1])
    coverage = tuple(replace(c, count=0, total=D("0.00")) for c in s.coverage)
    result = run(finance, replace(s, commitments=(), coverage=coverage))
    assert result.status == "INPUTS_VALIDATED"
    assert all(w.closing == D("650.00") for w in result.weeks)


@pytest.mark.parametrize("changes,reason", [
    ({"restriction": "RESTRICTED"}, "RESTRICTED_COMMITMENT"),
    ({"restriction": "BOARD_DESIGNATED"}, "RESTRICTED_COMMITMENT"),
    ({"state": "pending"}, "UNAPPROVED_OR_PAID_COMMITMENT"),
    ({"state": "PAID"}, "UNAPPROVED_OR_PAID_COMMITMENT"),
    ({"source_model": "billing.Invoice"}, "NONCANONICAL_CASH_SOURCE"),
    ({"source_model": "ledger.Charge"}, "NONCANONICAL_CASH_SOURCE"),
    ({"kind": "invoice"}, "NONCANONICAL_CASH_SOURCE"),
    ({"kind": "allocation"}, "NONCANONICAL_CASH_SOURCE"),
    ({"kind": "credit"}, "NONCANONICAL_CASH_SOURCE"),
    ({"kind": "payment"}, "NONCANONICAL_CASH_SOURCE"),
    ({"obligation_id": ""}, "MISSING_CANONICAL_IDENTITY"),
    ({"due_on": None}, "UNDATED_OR_OUT_OF_HORIZON_COMMITMENT"),
    ({"due_on": CUTOFF}, "UNDATED_OR_OUT_OF_HORIZON_COMMITMENT"),
    ({"due_on": START + timedelta(days=91)}, "UNDATED_OR_OUT_OF_HORIZON_COMMITMENT"),
    ({"amount": D("0.00")}, "INVALID_COMMITMENT_AMOUNT"),
    ({"amount": D("-1.00")}, "INVALID_COMMITMENT_AMOUNT"),
    ({"amount": D("0.001")}, "INVALID_COMMITMENT_AMOUNT"),
])
def test_bad_commitments(finance, changes, reason):
    s = sample(finance[1])
    blocked(finance, replace(s, commitments=(replace(s.commitments[0], **changes),) + s.commitments[1:]), reason)


def test_duplicate_collections_and_overlap(finance):
    s = sample(finance[1])
    blocked(finance, replace(s, commitments=s.commitments + (s.commitments[0],)), "DUPLICATE_CASH_EVENT")
    shadow = replace(s.commitments[2], kind="recurring", source_id="payroll-shadow")
    blocked(finance, replace(s, commitments=s.commitments + (shadow,)), "DUPLICATE_OUTFLOW_OBLIGATION")
    # Different installment IDs still cannot exceed the charge's net balance.
    shadow = replace(s.commitments[0], source_id="installment-shadow")
    blocked(finance, replace(s, commitments=s.commitments + (shadow,)), "COLLECTION_EXCEEDS_NET_RECEIVABLE")


def test_net_receivable_linkage_and_non_cash_credit_limit(finance):
    s = sample(finance[1])
    blocked(finance, replace(s, receivables=()), "UNLINKED_TUITION_COLLECTION")
    blocked(finance, replace(s, receivables=s.receivables * 2), "DUPLICATE_OR_UNLINKED_RECEIVABLE")
    # Cash allocations and noncash aid lower the same outstanding obligation.
    blocked(finance, replace(s, receivables=(replace(s.receivables[0], outstanding=D("200.00")),)), "COLLECTION_EXCEEDS_NET_RECEIVABLE")


@pytest.mark.parametrize("state", ["pending", "authorized", "settling", "failed", "void", "reversed", "canceled"])
def test_unsettled_payments_never_available_cash(finance, state):
    s = sample(finance[1])
    blocked(finance, replace(s, payments=(replace(s.payments[0], state=state),)), "UNSETTLED_OR_REVERSED_PAYMENT")


def test_duplicate_settlements_and_refunds(finance):
    s = sample(finance[1])
    blocked(finance, replace(s, payments=s.payments * 2), "DUPLICATE_OR_UNIDENTIFIED_SETTLEMENT")
    shadow = replace(s.payments[0], payment_id="legacy-payment-shadow")
    blocked(finance, replace(s, payments=s.payments + (shadow,)), "DUPLICATE_OR_UNIDENTIFIED_SETTLEMENT")
    blocked(finance, replace(s, settlement_evidence=None), "MISSING_EVIDENCE")
    blocked(finance, replace(s, payments=(replace(s.payments[0], refunded=D("300.00")),)), "INVALID_SETTLEMENT_AMOUNT")
    blocked(finance, replace(s, payments=(replace(s.payments[0], state="settled"),)), "REFUND_STATE_MISMATCH")
    blocked(finance, replace(s, payments=(replace(s.payments[0], settled_on=START),)), "UNSETTLED_OR_AFTER_CUTOFF_PAYMENT")
    blocked(finance, replace(s, settlement_net=D("250.00")), "SETTLEMENT_RECONCILIATION_MISMATCH")


def test_full_refund_is_zero_and_not_future_cash(finance):
    s = sample(finance[1])
    payment = replace(s.payments[0], state="refunded", refunded=D("250.00"))
    result = run(finance, replace(s, payments=(payment,), settlement_net=D("0.00")))
    assert result.status == "INPUTS_VALIDATED"
    assert result.weeks[-1].closing == D("250.00")


def test_negative_balance_is_flagged_and_deterministic(finance):
    s = sample(finance[1])
    opening = replace(s.opening, bank_cash=D("350.00"), available=D("0.00"))
    result = run(finance, replace(s, opening=opening))
    assert result.weeks[-1].closing == D("-400.00")
    assert "NEGATIVE_AVAILABLE_CASH" in result.flags
    assert result == run(finance, replace(s, opening=opening, commitments=tuple(reversed(s.commitments))))


def test_caller_decimal_precision_does_not_round_cash(finance):
    s = sample(finance[1])
    expected = run(finance, s)
    with localcontext() as context:
        context.prec = 2
        assert run(finance, s) == expected
