from django.contrib.auth import get_user_model
from core.models import School
from rest_framework.test import APITestCase


class LearningContinuityApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create(username="learning-continuity-test@crown.local")
        self.user.set_password("pass1234")
        self.user.save(update_fields=["password"])
        self.school = School.objects.create(name="Learning Continuity Test School")
        self.user.school_id = str(self.school.id)
        self.client.force_authenticate(user=self.user)

    def _get(self, path):
        return self.client.get(path, HTTP_X_SCHOOL_ID=str(self.school.id))

    def test_online_command_contract_shape(self):
        response = self._get("/api/v1/learning-continuity/pages/onlineCommand/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["pageKey"], "onlineCommand")
        self.assertEqual(response.data["primarySource"], "CROWN")
        self.assertIn("authorityRules", response.data)
        self.assertIn("records", response.data)
        self.assertIn("workflow", response.data)
        self.assertIsInstance(response.data["authorityRules"], list)
        self.assertIsInstance(response.data["records"], list)
        self.assertIsInstance(response.data["workflow"], list)

    def test_teacher_cockpit_contract_shape(self):
        response = self._get("/api/v1/learning-continuity/pages/teacherCockpit/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["pageKey"], "teacherCockpit")
        self.assertEqual(response.data["primarySource"], "CROWN")

    def test_parent_status_contract_shape(self):
        response = self._get("/api/v1/learning-continuity/pages/parentStatus/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["pageKey"], "parentStatus")
        self.assertEqual(response.data["primarySource"], "CROWN")

    def test_unknown_page_returns_404(self):
        response = self._get("/api/v1/learning-continuity/pages/notARealPage/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "unknown_learning_continuity_page")

    def test_learning_continuity_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/v1/learning-continuity/pages/onlineCommand/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        self.assertEqual(response.status_code, 401)
