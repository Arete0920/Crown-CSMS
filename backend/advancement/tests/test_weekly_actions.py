"""Tenant-isolated and permission-scoped Advancement weekly action queue."""
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from advancement.models import Donor
from advancement.models_stage3 import Move, Prospect
from core.models import CrownPermission, RolePermission, School, UserRole


@override_settings(TENANT_HEADER_REQUIRED=True)
class WeeklyActionTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Advancement A")
        self.other = School.objects.create(name="Advancement B")
        self.user = get_user_model().objects.create_user(username=f"adv-{uuid4().hex[:8]}", school=self.school)
        UserRole.objects.create(user=self.user, school=self.school, role_code="HEAD_OF_SCHOOL")
        permission, _ = CrownPermission.objects.get_or_create(code="advancement.view")
        RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse("advancement-summary")
        self.today = timezone.localdate()

    def make_move(self, school, offset, *, completed=False, donor=None, assigned_to=None):
        if donor is None:
            donor = Donor.objects.create(school_id=school.id, name=f"Donor {offset}")
        prospect = Prospect.objects.create(
            school_id=school.id, donor=donor, assigned_to=assigned_to
        )
        return Move.objects.create(
            school_id=school.id,
            prospect=prospect,
            action_type="call",
            due_date=self.today + timedelta(days=offset),
            completed_at=timezone.now() if completed else None,
        )

    def get_actions(self):
        result = self.client.get(self.url, HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(result.status_code, 200, result.content)
        return result.json()["weekly_actions"]

    def test_empty_queue(self):
        self.assertEqual(self.get_actions(), [])

    def test_overdue_and_next_seven_days_only_sorted(self):
        future = self.make_move(self.school, 7)
        overdue = self.make_move(self.school, -2)
        self.make_move(self.school, 8)
        self.make_move(self.school, -1, completed=True)
        actions = self.get_actions()
        self.assertEqual([entry["id"] for entry in actions], [str(overdue.id), str(future.id)])
        self.assertEqual([entry["overdue"] for entry in actions], [True, False])

    def test_cross_school_moves_and_cross_school_donor_not_exposed(self):
        self.make_move(self.other, -1)
        # A corrupted move tenant must not expose its foreign prospect.
        crossed = self.make_move(self.other, -1)
        crossed.school_id = self.school.id
        crossed.save(update_fields=["school_id"])
        outside_donor = Donor.objects.create(school_id=self.other.id, name="Outside donor")
        mismatched = self.make_move(self.school, 1, donor=outside_donor)
        actions = self.get_actions()
        self.assertEqual([action["id"] for action in actions], [str(mismatched.id)])
        self.assertIsNone(actions[0]["donor_name"])

    def test_assigned_name_only_when_user_has_membership(self):
        outside_user = get_user_model().objects.create_user(username=f"outside-{uuid4().hex[:8]}")
        outsider = self.make_move(self.school, 1, assigned_to=outside_user)
        staff = self.make_move(self.school, 2, assigned_to=self.user)
        actions = self.get_actions()
        self.assertEqual([a["id"] for a in actions], [str(outsider.id), str(staff.id)])
        self.assertIsNone(actions[0]["owner"])
        self.assertEqual(actions[1]["owner"], self.user.get_username())

    def test_real_bearer_token_uses_drf_school_permission(self):
        """The dashboard sends a Bearer token, not a Django session cookie."""
        from rest_framework_simplejwt.tokens import RefreshToken

        jwt_client = APIClient()
        jwt_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        allowed = jwt_client.get(self.url)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["weekly_actions"], [])

        other = jwt_client.get(
            self.url, HTTP_X_SCHOOL_ID=str(self.other.id)
        )
        self.assertIn(other.status_code, (403, 404))

    def test_missing_grant_is_forbidden(self):
        RolePermission.objects.filter(
            role_code="HEAD_OF_SCHOOL", permission__code="advancement.view"
        ).delete()
        result = self.client.get(self.url, HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(result.status_code, 403)

    def test_other_school_header_does_not_borrow_access(self):
        response = self.client.get(self.url, HTTP_X_SCHOOL_ID=str(self.other.id))
        self.assertIn(response.status_code, (403, 404))
