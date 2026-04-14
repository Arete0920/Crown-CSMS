import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import School


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()
BASE = "/api/v1/staff-setup-wizard/sessions/"


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/New_York", is_active=True)


def _user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:6]}", password=TEST_AUTH_SECRET)


def _authed():
    c = APIClient()
    c.force_authenticate(user=_user())
    return c


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


class StaffWizardSmoke(TestCase):
    def test_happy(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        self.assertEqual(r.status_code, 201)
        sid = r.data["session_id"]

        roster = [{"email": "a@x.com", "first_name": "A", "is_teacher": True}]
        r2 = c.post(f"{BASE}{sid}/configure/", {"roster": roster}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 200)

        r3 = c.post(f"{BASE}{sid}/commit/", format="json", **_hdr(s.id))
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["total"], 1)

        r4 = c.get(f"{BASE}{sid}/verify/", **_hdr(s.id))
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.data["count"], 1)

    def test_empty_roster_rejected(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE}{sid}/configure/", {"roster": []}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 400)

    def test_idempotent_commit(self):
        s = _school()
        c = _authed()
        roster = [{"email": "b@x.com", "is_teacher": True}]
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        c.post(f"{BASE}{sid}/configure/", {"roster": roster}, format="json", **_hdr(s.id))
        c.post(f"{BASE}{sid}/commit/", format="json", **_hdr(s.id))
        # Second session with same email = update
        r2 = c.post(BASE, **_hdr(s.id))
        sid2 = r2.data["session_id"]
        c.post(f"{BASE}{sid2}/configure/", {"roster": roster}, format="json", **_hdr(s.id))
        r3 = c.post(f"{BASE}{sid2}/commit/", format="json", **_hdr(s.id))
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["updated"], 1)
