from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import NotFound

from core.models import School, UserRole
from households.scoping import MissingSchoolContext, get_request_school_id

User = get_user_model()


class CanonicalHouseholdScopingTests(TestCase):
    """Prove household scoping follows the immutable canonical tenant contract."""

    def setUp(self):
        self.factory = RequestFactory()
        self.school_a = School.objects.create(name="Scoping School A")
        self.school_b = School.objects.create(name="Scoping School B")
        self.user_a = User.objects.create_user(
            username="scoping-user-a",
            email="scoping-user-a@example.com",
            password="test-password",
            school=self.school_a,
        )
        self.staff_a = User.objects.create_user(
            username="scoping-staff-a",
            email="scoping-staff-a@example.com",
            password="test-password",
            school=self.school_a,
            is_staff=True,
        )
        self.support_a = User.objects.create_user(
            username="scoping-support-a",
            email="scoping-support-a@example.com",
            password="test-password",
            school=self.school_a,
            is_staff=True,
        )
        UserRole.objects.create(
            school=self.school_a,
            user=self.support_a,
            role_code="SUPPORT",
        )

    def _request(self, user=None, school_id=None):
        headers = {}
        if school_id is not None:
            headers["HTTP_X_SCHOOL_ID"] = str(school_id)
        request = self.factory.get("/api/v1/households/", **headers)
        if user is not None:
            request.user = user
        return request

    def test_principal_school_resolves_without_header(self):
        request = self._request(user=self.user_a)
        self.assertEqual(get_request_school_id(request), self.school_a.id)
        self.assertEqual(request.crown_tenant.school_id, self.school_a.id)

    def test_matching_header_resolves(self):
        request = self._request(user=self.user_a, school_id=self.school_a.id)
        self.assertEqual(get_request_school_id(request), self.school_a.id)

    def test_ordinary_user_cross_school_header_is_hidden(self):
        request = self._request(user=self.user_a, school_id=self.school_b.id)
        with self.assertRaises(NotFound):
            get_request_school_id(request)

    def test_staff_status_alone_is_not_override_authority(self):
        request = self._request(user=self.staff_a, school_id=self.school_b.id)
        with self.assertRaises(NotFound):
            get_request_school_id(request)

    def test_support_role_can_override_tenant(self):
        request = self._request(user=self.support_a, school_id=self.school_b.id)
        self.assertEqual(get_request_school_id(request), self.school_b.id)
        self.assertTrue(request.crown_tenant.override_authorized)

    def test_malformed_header_fails_closed(self):
        request = self.factory.get(
            "/api/v1/households/",
            HTTP_X_SCHOOL_ID="not-a-uuid",
        )
        request.user = self.user_a
        with self.assertRaises(MissingSchoolContext):
            get_request_school_id(request)
