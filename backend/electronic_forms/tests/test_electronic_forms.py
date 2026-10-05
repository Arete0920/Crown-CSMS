from copy import deepcopy
import uuid

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from electronic_forms.models import (
    ElectronicEnvelope,
    ElectronicFormTemplate,
    ElectronicSigner,
    ElectronicSignatureEvidence,
    canonical_document_hash,
)
from electronic_forms.services import (
    ELECTRONIC_CONSENT_VERSION,
    add_signer,
    create_envelope,
    record_consent,
    request_paper_copy,
    send_envelope,
    sign_envelope,
)


pytestmark = pytest.mark.django_db


def _user(*, school, prefix):
    return UserAccount.objects.create_user(
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.org",
        password="test-only-password",
        school=school,
    )


def _grant_manage(*, user, school, role_code):
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(code="forms.manage")
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _template(*, school, creator):
    return ElectronicFormTemplate.objects.create(
        school=school,
        key="enrollment-agreement",
        version=1,
        name="Enrollment Agreement",
        title="2027 Enrollment Agreement",
        body="Agreement body {{student_name}}",
        form_schema={"student_name": {"type": "string", "required": True}},
        created_by=creator,
    )


def _sent_envelope(*, school, creator, signer_user):
    template = _template(school=school, creator=creator)
    envelope = create_envelope(
        template=template,
        created_by=creator,
        form_data={"student_name": "Jordan Reed"},
        subject_type="application",
        subject_id="APP-1001",
    )
    signer = add_signer(
        envelope=envelope,
        user=signer_user,
        display_name="Pat Reed",
        email=signer_user.email,
        role_label="Parent/Guardian",
    )
    envelope = send_envelope(envelope)
    signer.refresh_from_db()
    return envelope, signer


def test_document_hash_is_deterministic_and_snapshot_is_immutable():
    school = School.objects.create(name="Electronic Forms Hash School")
    manager = _user(school=school, prefix="hash-manager")
    signer_user = _user(school=school, prefix="hash-signer")
    envelope, _ = _sent_envelope(school=school, creator=manager, signer_user=signer_user)

    assert envelope.document_sha256 == canonical_document_hash(envelope.document_snapshot)

    tampered = deepcopy(envelope.document_snapshot)
    tampered["data"]["student_name"] = "Changed Name"
    envelope.document_snapshot = tampered
    with pytest.raises(ValidationError):
        envelope.save()


def test_signing_requires_current_electronic_consent_and_explicit_intent():
    school = School.objects.create(name="Electronic Consent School")
    manager = _user(school=school, prefix="consent-manager")
    signer_user = _user(school=school, prefix="consent-signer")
    envelope, signer = _sent_envelope(school=school, creator=manager, signer_user=signer_user)

    with pytest.raises(ValidationError):
        sign_envelope(
            signer=signer,
            user=signer_user,
            signed_name="Pat Reed",
            intent_to_sign=True,
        )

    with pytest.raises(ValidationError):
        record_consent(
            signer=signer,
            user=signer_user,
            disclosure_version="stale-version",
            hardware_software_ack=True,
        )

    consent = record_consent(
        signer=signer,
        user=signer_user,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
    )
    assert consent.action == ElectronicSignatureEvidence.Action.CONSENT

    signer.refresh_from_db()
    with pytest.raises(ValidationError):
        sign_envelope(
            signer=signer,
            user=signer_user,
            signed_name="Pat Reed",
            intent_to_sign=False,
        )

    signature = sign_envelope(
        signer=signer,
        user=signer_user,
        signed_name="Pat Reed",
        intent_to_sign=True,
    )
    assert signature.action == ElectronicSignatureEvidence.Action.SIGN
    assert signature.document_sha256 == envelope.document_sha256
    assert signature.intent_statement

    envelope.refresh_from_db()
    signer.refresh_from_db()
    assert signer.status == ElectronicSigner.Status.SIGNED
    assert envelope.status == ElectronicEnvelope.Status.COMPLETED


def test_only_assigned_signer_may_consent_or_sign():
    school = School.objects.create(name="Signer Attribution School")
    manager = _user(school=school, prefix="attrib-manager")
    signer_user = _user(school=school, prefix="attrib-signer")
    imposter = _user(school=school, prefix="attrib-imposter")
    _, signer = _sent_envelope(school=school, creator=manager, signer_user=signer_user)

    with pytest.raises(ValidationError):
        record_consent(
            signer=signer,
            user=imposter,
            disclosure_version=ELECTRONIC_CONSENT_VERSION,
            hardware_software_ack=True,
        )


def test_signature_evidence_is_append_only_and_retained():
    school = School.objects.create(name="Evidence Retention School")
    manager = _user(school=school, prefix="retain-manager")
    signer_user = _user(school=school, prefix="retain-signer")
    _, signer = _sent_envelope(school=school, creator=manager, signer_user=signer_user)

    evidence = record_consent(
        signer=signer,
        user=signer_user,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
    )
    evidence.consent_text = "changed"
    with pytest.raises(ValidationError):
        evidence.save()
    with pytest.raises(ValidationError):
        evidence.delete()


def test_paper_copy_request_is_recorded_without_destroying_document():
    school = School.objects.create(name="Paper Copy School")
    manager = _user(school=school, prefix="paper-manager")
    signer_user = _user(school=school, prefix="paper-signer")
    envelope, signer = _sent_envelope(school=school, creator=manager, signer_user=signer_user)

    evidence = request_paper_copy(signer=signer, user=signer_user)
    assert evidence.action == ElectronicSignatureEvidence.Action.PAPER_COPY_REQUEST
    signer.refresh_from_db()
    envelope.refresh_from_db()
    assert signer.status == ElectronicSigner.Status.PAPER_REQUESTED
    assert envelope.document_sha256 == canonical_document_hash(envelope.document_snapshot)


def test_api_manager_can_issue_and_assigned_signer_can_retrieve_exact_record():
    school = School.objects.create(name="Electronic Forms API School")
    manager = _user(school=school, prefix="api-manager")
    signer_user = _user(school=school, prefix="api-signer")
    unrelated = _user(school=school, prefix="api-unrelated")
    _grant_manage(user=manager, school=school, role_code="forms_test_manager")

    manager_client = APIClient()
    manager_client.force_authenticate(manager)

    template_response = manager_client.post(
        "/api/v1/forms/templates/",
        {
            "key": "permission-form",
            "version": 1,
            "name": "Permission Form",
            "title": "Permission Form",
            "body": "I authorize the stated activity.",
            "form_schema": {},
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert template_response.status_code == 201, template_response.content

    issue_response = manager_client.post(
        "/api/v1/forms/envelopes/",
        {
            "template_id": template_response.json()["id"],
            "subject_type": "student_activity",
            "subject_id": "ACT-100",
            "form_data": {"activity": "Field Trip"},
            "signers": [
                {
                    "user_id": str(signer_user.id),
                    "display_name": "Assigned Parent",
                    "email": signer_user.email,
                    "role_label": "Parent/Guardian",
                }
            ],
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert issue_response.status_code == 201, issue_response.content
    envelope_id = issue_response.json()["id"]
    document_hash = issue_response.json()["document_sha256"]

    signer_client = APIClient()
    signer_client.force_authenticate(signer_user)
    detail = signer_client.get(
        f"/api/v1/forms/envelopes/{envelope_id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert detail.status_code == 200
    assert detail.json()["document_sha256"] == document_hash
    assert detail.json()["document_snapshot"]["data"]["activity"] == "Field Trip"

    unrelated_client = APIClient()
    unrelated_client.force_authenticate(unrelated)
    denied = unrelated_client.get(
        f"/api/v1/forms/envelopes/{envelope_id}/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert denied.status_code == 403


def test_cross_school_manager_cannot_access_other_school_envelope():
    school_a = School.objects.create(name="Forms School A")
    school_b = School.objects.create(name="Forms School B")
    manager_a = _user(school=school_a, prefix="manager-a")
    manager_b = _user(school=school_b, prefix="manager-b")
    signer_user = _user(school=school_a, prefix="signer-a")
    _grant_manage(user=manager_a, school=school_a, role_code="forms_manager_a")
    _grant_manage(user=manager_b, school=school_b, role_code="forms_manager_b")
    envelope, _ = _sent_envelope(school=school_a, creator=manager_a, signer_user=signer_user)

    client = APIClient()
    client.force_authenticate(manager_b)
    response = client.get(
        f"/api/v1/forms/envelopes/{envelope.id}/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    assert response.status_code == 404


def test_template_version_is_immutable_after_creation():
    school = School.objects.create(name="Immutable Template School")
    manager = _user(school=school, prefix="immutable-manager")
    template = _template(school=school, creator=manager)

    template.body = "Changed body"
    with pytest.raises(ValidationError):
        template.save()


def test_api_envelope_issue_rolls_back_if_any_signer_is_invalid():
    school = School.objects.create(name="Envelope Atomic School")
    manager = _user(school=school, prefix="atomic-manager")
    valid_signer = _user(school=school, prefix="atomic-signer")
    _grant_manage(user=manager, school=school, role_code="forms_atomic_manager")
    template = _template(school=school, creator=manager)

    client = APIClient()
    client.force_authenticate(manager)
    response = client.post(
        "/api/v1/forms/envelopes/",
        {
            "template_id": str(template.id),
            "form_data": {"student_name": "Jordan Reed"},
            "signers": [
                {
                    "user_id": str(valid_signer.id),
                    "display_name": "Valid Signer",
                },
                {
                    "user_id": str(uuid.uuid4()),
                    "display_name": "Missing Signer",
                },
            ],
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 409
    assert ElectronicEnvelope.objects.filter(school=school).count() == 0
    assert ElectronicSigner.objects.filter(school=school).count() == 0
