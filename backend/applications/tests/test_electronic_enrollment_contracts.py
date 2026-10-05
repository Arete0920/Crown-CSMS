from __future__ import annotations

from datetime import date
import uuid

import pytest
from django.core.exceptions import ValidationError

from applications.electronic_contracts import (
    assert_contract_can_be_countersigned,
    ensure_enrollment_contract_envelope,
    void_pending_enrollment_contract_envelope,
)
from applications.models import (
    Application,
    ApplicationEvent,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from applications import views_admissions as admissions
from core.models import School, UserAccount
from electronic_forms.models import ElectronicEnvelope, ElectronicSigner
from electronic_forms.services import (
    ELECTRONIC_CONSENT_VERSION,
    record_consent,
    sign_envelope,
)
from households.models import Guardian, Household


pytestmark = pytest.mark.django_db


def _user(*, school: School, prefix: str) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.org",
        password="test-only-password",
        school=school,
    )


def _application_with_guardian(*, school: School, manager: UserAccount, parent: UserAccount):
    household = Household.objects.create(
        school_id=school.id,
        name="Electronic Contract Family",
        address1="100 Test Lane",
        city="Wilmington",
        state="DE",
        postal_code="19801",
        is_active=True,
    )
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=parent,
        first_name="Pat",
        last_name="Guardian",
        email=parent.email,
        is_primary=True,
    )
    app = Application.objects.create(
        school_id=school.id,
        household=household,
        status="DECIDED",
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=app,
        event_type="decision_made",
        payload={"decision": "accepted", "updated_by": manager.email},
    )
    return app


def _issued_contract(*, school: School, app: Application, manager: UserAccount):
    contract = EnrollmentContract.objects.create(
        school_id=school.id,
        application=app,
        version=1,
        status=EnrollmentContractStatus.ISSUED,
        line_items=[
            {"label": "Tuition", "category": "tuition", "amount_cents": 1_000_000},
            {"label": "Deposit", "category": "deposit", "amount_cents": 25_000},
        ],
        contract_totals={
            "gross_tuition_cents": 1_000_000,
            "fees_cents": 0,
            "discounts_cents": 0,
            "aid_cents": 0,
            "scholarships_cents": 0,
            "esa_voucher_tax_credit_cents": 0,
            "donor_assistance_cents": 0,
            "deposit_cents": 25_000,
            "amount_due_today_cents": 25_000,
            "net_family_obligation_cents": 975_000,
        },
        net_amount_cents=975_000,
        currency="USD",
        payment_plan="Monthly",
        payment_schedule="10 monthly installments",
        responsible_payer="Parent/Guardian",
        refund_terms="School-approved refund terms.",
        note="Enrollment contract test record.",
        created_by=manager.email,
    )
    return contract


def _setup_contract():
    school = School.objects.create(name="Electronic Contract School")
    manager = _user(school=school, prefix="contract-manager")
    parent = _user(school=school, prefix="contract-parent")
    app = _application_with_guardian(
        school=school,
        manager=manager,
        parent=parent,
    )
    contract = _issued_contract(
        school=school,
        app=app,
        manager=manager,
    )
    return school, manager, parent, app, contract


def test_issued_contract_creates_exact_hashed_envelope_for_authenticated_guardian():
    school, manager, parent, app, contract = _setup_contract()

    envelope = ensure_enrollment_contract_envelope(
        contract=contract,
        actor_user=manager,
    )
    contract.refresh_from_db()

    assert contract.electronic_envelope_id == envelope.id
    assert envelope.school_id == school.id
    assert envelope.subject_type == "enrollment_contract"
    assert envelope.subject_id == str(contract.id)
    assert envelope.status == ElectronicEnvelope.Status.SENT
    assert envelope.document_sha256
    assert envelope.document_snapshot["data"]["contract_id"] == str(contract.id)
    assert envelope.document_snapshot["data"]["contract_version"] == 1
    assert envelope.document_snapshot["data"]["contract_totals"]["net_family_obligation_cents"] == 975_000

    signer = envelope.signers.get()
    assert signer.user_id == parent.id
    assert signer.school_id == school.id
    assert signer.status == ElectronicSigner.Status.PENDING


def test_contract_issue_fails_closed_without_authenticated_guardian_account():
    school = School.objects.create(name="Missing Guardian Account School")
    manager = _user(school=school, prefix="missing-manager")
    household = Household.objects.create(
        school_id=school.id,
        name="No Account Family",
        address1="200 Test Lane",
        city="Wilmington",
        state="DE",
        postal_code="19801",
        is_active=True,
    )
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="No",
        last_name="Account",
        email="no-account@example.org",
        is_primary=True,
    )
    app = Application.objects.create(
        school_id=school.id,
        household=household,
        status="DECIDED",
    )
    contract = _issued_contract(school=school, app=app, manager=manager)

    with pytest.raises(ValidationError, match="authenticated guardian"):
        ensure_enrollment_contract_envelope(contract=contract, actor_user=manager)

    contract.refresh_from_db()
    assert contract.electronic_envelope_id is None
    assert not ElectronicEnvelope.objects.filter(school=school).exists()


def test_staff_cannot_mark_enrollment_contract_signed_without_signature_evidence():
    _, _, _, _, contract = _setup_contract()

    with pytest.raises(ValidationError, match="electronic signature evidence"):
        admissions._validate_contract_record_mutation(
            latest=contract,
            requested_status=EnrollmentContractStatus.SIGNED.value,
            payload={"status": EnrollmentContractStatus.SIGNED.value},
        )


def test_guardian_signature_completes_envelope_and_marks_contract_signed():
    _, manager, parent, app, contract = _setup_contract()
    envelope = ensure_enrollment_contract_envelope(
        contract=contract,
        actor_user=manager,
    )
    signer = envelope.signers.get()

    record_consent(
        signer=signer,
        user=parent,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
    )
    signer.refresh_from_db()
    sign_envelope(
        signer=signer,
        user=parent,
        signed_name="Pat Guardian",
        intent_to_sign=True,
    )

    envelope.refresh_from_db()
    contract.refresh_from_db()

    assert envelope.status == ElectronicEnvelope.Status.COMPLETED
    assert contract.status == EnrollmentContractStatus.SIGNED
    assert contract.signed_at is not None

    evidence_event = ApplicationEvent.objects.get(
        school_id=contract.school_id,
        application=app,
        event_type="contract_signed_electronically",
    )
    assert evidence_event.payload["electronic_envelope_id"] == str(envelope.id)
    assert evidence_event.payload["document_sha256"] == envelope.document_sha256

    workflow_event = (
        ApplicationEvent.objects.filter(
            school_id=contract.school_id,
            application=app,
            event_type="enrollment_state_updated",
        )
        .order_by("-created_at")
        .first()
    )
    assert workflow_event.payload["contract_status"] == "signed"
    assert workflow_event.payload["electronic_envelope_id"] == str(envelope.id)


def test_countersignature_requires_completed_electronic_signature():
    _, manager, parent, _, contract = _setup_contract()
    ensure_enrollment_contract_envelope(contract=contract, actor_user=manager)
    contract.refresh_from_db()

    with pytest.raises(ValidationError, match="electronically signed"):
        assert_contract_can_be_countersigned(contract)

    signer = contract.electronic_envelope.signers.get()
    record_consent(
        signer=signer,
        user=parent,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
    )
    signer.refresh_from_db()
    sign_envelope(
        signer=signer,
        user=parent,
        signed_name="Pat Guardian",
        intent_to_sign=True,
    )

    contract.refresh_from_db()
    assert_contract_can_be_countersigned(contract)


def test_issued_contract_terms_are_immutable_and_require_amendment():
    _, manager, _, _, contract = _setup_contract()
    ensure_enrollment_contract_envelope(contract=contract, actor_user=manager)
    contract.refresh_from_db()

    with pytest.raises(ValidationError, match="immutable after signature delivery"):
        admissions._validate_contract_record_mutation(
            latest=contract,
            requested_status=EnrollmentContractStatus.ISSUED.value,
            payload={"payment_plan": "Changed plan"},
        )


def test_pending_envelope_is_voided_before_amendment_reissue():
    school, manager, _, app, contract = _setup_contract()
    envelope = ensure_enrollment_contract_envelope(
        contract=contract,
        actor_user=manager,
    )

    void_pending_enrollment_contract_envelope(contract)
    envelope.refresh_from_db()
    assert envelope.status == ElectronicEnvelope.Status.VOID

    contract.status = EnrollmentContractStatus.SUPERSEDED
    contract.save(update_fields=["status", "updated_at"])

    amended = EnrollmentContract.objects.create(
        school_id=school.id,
        application=app,
        version=2,
        status=EnrollmentContractStatus.ISSUED,
        line_items=contract.line_items,
        contract_totals={**contract.contract_totals, "fees_cents": 10_000},
        net_amount_cents=985_000,
        currency="USD",
        payment_plan="Monthly",
        payment_schedule="10 monthly installments",
        responsible_payer="Parent/Guardian",
        refund_terms="Amended refund terms.",
        note="Amended contract.",
        amended_from=contract,
        created_by=manager.email,
    )
    new_envelope = ensure_enrollment_contract_envelope(
        contract=amended,
        actor_user=manager,
    )

    assert new_envelope.id != envelope.id
    assert new_envelope.status == ElectronicEnvelope.Status.SENT
    assert new_envelope.document_snapshot["data"]["contract_version"] == 2
    assert new_envelope.document_sha256 != envelope.document_sha256


def test_cross_school_guardian_account_is_rejected_at_model_boundary():
    school_a = School.objects.create(name="Contract School A")
    school_b = School.objects.create(name="Contract School B")
    manager = _user(school=school_a, prefix="cross-manager")
    foreign_parent = _user(school=school_b, prefix="cross-parent")
    household = Household.objects.create(
        school_id=school_a.id,
        name="Cross School Family",
        address1="300 Test Lane",
        city="Wilmington",
        state="DE",
        postal_code="19801",
        is_active=True,
    )

    with pytest.raises(ValidationError):
        Guardian.objects.create(
            school_id=school_a.id,
            household=household,
            account=foreign_parent,
            first_name="Cross",
            last_name="Tenant",
            email=foreign_parent.email,
            is_primary=True,
        )

    app = Application.objects.create(
        school_id=school_a.id,
        household=household,
        status="DECIDED",
    )
    contract = _issued_contract(school=school_a, app=app, manager=manager)
    with pytest.raises(ValidationError, match="authenticated guardian"):
        ensure_enrollment_contract_envelope(contract=contract, actor_user=manager)
