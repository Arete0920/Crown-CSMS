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
