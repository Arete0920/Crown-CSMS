import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import School

User = get_user_model()
BASE = "/api/v1/room-setup-wizard/sessions/"


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/New_York", is_active=True)


def _user():
    return User.objects.create_user(username=f"u{uuid.uuid4().hex[:6]}", password="pw")


def _authed():
    c = APIClient()
    c.force_authenticate(user=_user())
    return c


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


class RoomWizardSmoke(TestCase):
    def test_happy(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        self.assertEqual(r.status_code, 201)
        sid = r.data["session_id"]

        rooms = [{"code": "101", "name": "Room 101", "capacity": 24}]
        r2 = c.post(f"{BASE}{sid}/configure/", {"rooms": rooms}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 200)

        r3 = c.post(f"{BASE}{sid}/commit/", format="json", **_hdr(s.id))
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["total"], 1)

        r4 = c.get(f"{BASE}{sid}/verify/", **_hdr(s.id))
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.data["count"], 1)

    def test_negative_capacity_rejected(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE}{sid}/configure/", {"rooms": [{"code": "X", "capacity": -1}]}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 400)

    def test_missing_code_rejected(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        r2 = c.post(f"{BASE}{sid}/configure/", {"rooms": [{"code": "", "capacity": 10}]}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 400)
