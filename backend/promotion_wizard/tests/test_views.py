import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import School


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

User = get_user_model()
BASE = "/api/v1/promotion-wizard/sessions/"


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


class PromotionWizardSmoke(TestCase):
    def test_happy(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        self.assertEqual(r.status_code, 201)
        sid = r.data["session_id"]

        rules = [{"from_grade_code": "K", "to_grade_code": "1", "ordering": 0}]
        r2 = c.post(f"{BASE}{sid}/configure/", {"rules": rules}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 200)

        r3 = c.post(f"{BASE}{sid}/commit/", format="json", **_hdr(s.id))
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["total"], 1)

        r4 = c.get(f"{BASE}{sid}/verify/", **_hdr(s.id))
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.data["count"], 1)

    def test_invalid_grade_rejected(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        r2 = c.post(
            f"{BASE}{sid}/configure/",
            {"rules": [{"from_grade_code": "ZZ", "to_grade_code": "1", "ordering": 0}]},
            format="json",
            **_hdr(s.id),
        )
        self.assertEqual(r2.status_code, 400)

    def test_duplicate_from_grade_rejected(self):
        s = _school()
        c = _authed()
        r = c.post(BASE, **_hdr(s.id))
        sid = r.data["session_id"]
        rules = [
            {"from_grade_code": "K", "to_grade_code": "1", "ordering": 0},
            {"from_grade_code": "K", "to_grade_code": "2", "ordering": 1},
        ]
        r2 = c.post(f"{BASE}{sid}/configure/", {"rules": rules}, format="json", **_hdr(s.id))
        self.assertEqual(r2.status_code, 400)
