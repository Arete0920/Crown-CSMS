import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from advancement.models import Event, Ticket
from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school(name):
    return School.objects.create(name=name)


def _user(school, email):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"crownpass-{token}",
        email=email,
        password="Passw0rd!",
        school=school,
    )


def _event(school, name):
    from django.utils import timezone

    return Event.objects.create(
        school_id=school.id,
        name=name,
        date=timezone.now(),
        location="Main Gym",
        ticket_price="10.00",
        capacity=500,
        active=True,
    )


def _ticket(school, event, *, email, name="Parent"):
    return Ticket.objects.create(
        school_id=school.id,
        event=event,
        purchaser_name=name,
        purchaser_email=email,
        qr_code=f"qr-{uuid.uuid4()}",
    )


class TestCrownPassFamilyTicketsApi:
    def setup_method(self):
        self.school = _school("CrownPass School")
        self.other_school = _school("Other CrownPass School")
        self.user = _user(self.school, "parent@example.com")
        self.client = APIClient()

    def test_requires_authentication(self):
        response = self.client.get(
            "/api/v1/crownpass/my-tickets/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (401, 403)

    def test_returns_only_authenticated_users_email_in_asserted_tenant(self):
        own_event = _event(self.school, "Varsity Basketball")
        other_event = _event(self.school, "School Play")
        foreign_event = _event(self.other_school, "Other School Game")

        own_ticket = _ticket(
            self.school,
            own_event,
            email="parent@example.com",
        )
        _ticket(
            self.school,
            other_event,
            email="someone-else@example.com",
        )
        _ticket(
            self.other_school,
            foreign_event,
            email="parent@example.com",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/crownpass/my-tickets/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["tickets"][0]["ticket_id"] == str(own_ticket.id)
        assert payload["tickets"][0]["event_name"] == "Varsity Basketball"

    def test_does_not_expose_raw_qr_credential(self):
        event = _event(self.school, "Varsity Football")
        _ticket(
            self.school,
            event,
            email="parent@example.com",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/crownpass/my-tickets/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 200
        ticket = response.json()["tickets"][0]
        assert "qr_code" not in ticket
        assert "credential" not in ticket


    def test_owned_ticket_credential_returns_signed_qr_not_legacy_qr(self):
        event = _event(self.school, "Homecoming")
        ticket = _ticket(
            self.school,
            event,
            email="parent@example.com",
        )
        legacy_qr = ticket.qr_code

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/crownpass/my-tickets/{ticket.id}/credential/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ticket_id"] == str(ticket.id)
        assert payload["credential_type"] == "signed-v1"
        assert payload["credential"] != legacy_qr
        assert legacy_qr not in payload["credential"]
        assert payload["qr_data_url"].startswith("data:image/png;base64,")

    def test_cannot_request_another_users_ticket_credential(self):
        event = _event(self.school, "Spring Musical")
        ticket = _ticket(
            self.school,
            event,
            email="another-parent@example.com",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/crownpass/my-tickets/{ticket.id}/credential/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 404

    def test_cannot_request_cross_tenant_ticket_credential(self):
        event = _event(self.other_school, "Away Game")
        ticket = _ticket(
            self.other_school,
            event,
            email="parent@example.com",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/crownpass/my-tickets/{ticket.id}/credential/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 404

    def test_used_ticket_does_not_receive_new_credential(self):
        event = _event(self.school, "Tournament Final")
        ticket = _ticket(
            self.school,
            event,
            email="parent@example.com",
        )
        ticket.checked_in = True
        ticket.save(update_fields=["checked_in"])

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/crownpass/my-tickets/{ticket.id}/credential/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        assert response.status_code == 409


def test_signed_credential_tenant_binding_and_duplicate_redemption():
    from django.core import signing

    from crownpass.credentials import (
        credential_fingerprint,
        issue_admission_credential,
        verify_admission_credential,
    )
    from crownpass.services import redeem_ticket

    school = _school("Credential School")
    other_school = _school("Credential Other School")
    event = _event(school, "Varsity Soccer")
    ticket = _ticket(school, event, email="parent@example.com")

    credential = issue_admission_credential(ticket=ticket)
    payload = verify_admission_credential(credential=credential, school_id=school.id)
    assert payload["ticket_id"] == str(ticket.id)

    with pytest.raises(signing.BadSignature):
        verify_admission_credential(
            credential=credential,
            school_id=other_school.id,
        )

    first = redeem_ticket(
        school_id=school.id,
        ticket_id=ticket.id,
        scanned_by_id=None,
        attempted=credential_fingerprint(credential),
    )
    second = redeem_ticket(
        school_id=school.id,
        ticket_id=ticket.id,
        scanned_by_id=None,
        attempted=credential_fingerprint(credential),
    )

    assert first.result == "accepted"
    assert second.result == "duplicate"
