from datetime import datetime, timedelta, timezone, date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount, School, Family, Student
from crown_api.models import (
    Household,
    HouseholdMember,
    Message,
    MessageThread,
    Person,
    UserPersonLink,
)
from crown_api.models_households import ROLE_GUARDIAN


def _dt(y, m, d, hh, mm) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


class CommsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password="testpass",
            is_staff=False,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # Create core School and Family for core.models.Student
        self.school = School.objects.create(name="Test School")
        self.family_a = Family.objects.create(school=self.school, family_name="Family A")
        self.family_b = Family.objects.create(school=self.school, family_name="Family B")

        # Create core.models.Student objects
        self.student_a = Student.objects.create(
            school=self.school,
            family=self.family_a,
            student_number="STU001",
            first_name="Student",
            last_name="A",
            dob=date(2018, 1, 1),
            status='ACTIVE',
        )
        self.student_b = Student.objects.create(
            school=self.school,
            family=self.family_b,
            student_number="STU002",
            first_name="Student",
            last_name="B",
            dob=date(2017, 1, 1),
            status='ACTIVE',
        )

        other_person = Person.objects.create(
            first_name="Other",
            last_name="Guardian",
            email="other.guardian@example.com",
        )
        HouseholdMember.objects.create(
            household=self.household_b,
            person=other_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # 2 threads per household
        self.thread_a_household = MessageThread.objects.create(
            household=self.household_a,
            student=None,
            subject="Welcome",
            thread_type="GENERAL",
            created_by=self.parent_person,
        )
        self.thread_a_student = MessageThread.objects.create(
            household=self.household_a,
            student=self.student_a,
            subject="Attendance follow-up",
            thread_type="ATTENDANCE",
            created_by=self.parent_person,
        )

        self.thread_b_household = MessageThread.objects.create(
            household=self.household_b,
            student=None,
            subject="Billing reminder",
            thread_type="BILLING",
            created_by=other_person,
        )
        self.thread_b_student = MessageThread.objects.create(
            household=self.household_b,
            student=self.student_b,
            subject="General question",
            thread_type="GENERAL",
            created_by=other_person,
        )

        self._add_messages(self.thread_a_household, self.parent_person, _dt(2026, 1, 2, 12, 0))
        self._add_messages(self.thread_a_student, self.parent_person, _dt(2026, 1, 3, 12, 0))
        self._add_messages(self.thread_b_household, other_person, _dt(2026, 1, 4, 12, 0))
        self._add_messages(self.thread_b_student, other_person, _dt(2026, 1, 5, 12, 0))

    def _add_messages(self, thread: MessageThread, sender: Person, base: datetime) -> None:
        last_sent = None
        for i in range(3):
            sent_at = base + timedelta(minutes=i * 10)
            Message.objects.create(
                thread=thread,
                sender_person=sender,
                body=f"Msg {i + 1} for {thread.subject}",
                sent_at=sent_at,
            )
            last_sent = sent_at

        thread.last_message_at = last_sent
        thread.save(update_fields=["last_message_at", "updated_at"])

    def test_threads_list_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/threads/")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 4)

        ids = {row["thread_id"] for row in body}
        self.assertEqual(
            ids,
            {
                str(self.thread_a_household.id),
                str(self.thread_a_student.id),
                str(self.thread_b_household.id),
                str(self.thread_b_student.id),
            },
        )

    def test_thread_detail_staff_200_includes_messages(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(f"/api/threads/{self.thread_a_household.id}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["thread_id"], str(self.thread_a_household.id))
        self.assertIn("messages", body)
        self.assertEqual(len(body["messages"]), 3)

    def test_threads_list_parent_scoped_to_household(self):
        self.client.force_authenticate(user=self.parent_user)
        resp = self.client.get("/api/threads/")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertIsInstance(body, list)
        ids = {row["thread_id"] for row in body}
        self.assertEqual(ids, {str(self.thread_a_household.id), str(self.thread_a_student.id)})

    def test_thread_detail_parent_in_scope_200(self):
        self.client.force_authenticate(user=self.parent_user)
        resp = self.client.get(f"/api/threads/{self.thread_a_student.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_thread_detail_parent_out_of_scope_404(self):
        self.client.force_authenticate(user=self.parent_user)
        resp = self.client.get(f"/api/threads/{self.thread_b_household.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_threads_unauth_403(self):
        # IsAuthenticated + JWT configured → DRF emits 401 (not 403) for unauthenticated
        resp = self.client.get("/api/threads/")
        self.assertEqual(resp.status_code, 401)
