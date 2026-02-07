"""
Integration test for weighted grading transcript calculation.

**IMPORTANT**: These tests require demo seed data to be present.

To run these tests:
1. Load demo seed: `python seed_a535_clean.py`
2. Run tests against dev database: `python manage.py test test_weighted_transcript --settings=crown_api.settings_dev`

Or manually verify via curl/Postman using the proof script in curl_examples_director_actions.sh

Verifies:
1. Weighted grading affects transcript final_percent (76.3 with 40/30/20/10 distribution)
2. final_percent is null when assignment-to-category mapping is broken
3. Batch weight endpoint works atomically and rejects foreign category IDs

Relies on demo seed state:
- Section: 044882e0-3405-4542-a237-32f1adf4f047 (MATH-101, Ava Brooks)
- Student: da6e706b-ea3f-4047-aa0b-0dbcc0e4aac5
- School: b45b8c5a-6708-4597-aad9-a226627b2962
- GradeEntry rows: Final Exam (66/100), Quiz 1 (13/20), Quiz 2 (20/20), Homework 1 (8/10), Project 1 (46/50)
"""
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from academics.models import Assignment, AssignmentCategory

User = get_user_model()


class WeightedTranscriptIntegrationTest(TestCase):
    """Integration test using demo seed data."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up once for all tests - uses demo seed data."""
        cls.school_id = "b45b8c5a-6708-4597-aad9-a226627b2962"
        cls.section_id = "044882e0-3405-4542-a237-32f1adf4f047"
        cls.student_id = "da6e706b-ea3f-4047-aa0b-0dbcc0e4aac5"
        
    def setUp(self):
        """Set up API client and auth for each test."""
        self.client = APIClient()
        
        # Use existing head user from seed
        try:
            self.user = User.objects.get(username="head@crown-demo.local")
        except User.DoesNotExist:
            self.skipTest("Demo seed not loaded - run: python seed_a535_clean.py")
        
        # Verify section and student exist
        from academics.models import Section
        from households.models import Student
        
        if not Section.objects.filter(id=self.section_id).exists():
            self.skipTest("Demo section not found - run: python seed_a535_clean.py")
        
        if not Student.objects.filter(id=self.student_id).exists():
            self.skipTest("Demo student not found - run: python seed_a535_clean.py")
        
        self.client.force_authenticate(user=self.user)
    
    def test_weighted_grading_produces_76_3(self):
        """Test that weighted categories produce expected final_percent via API."""
        # Step 1: Create categories at weight=0
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "Exams", "weight_percent": "0.00", "sort_order": 1, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cat_exams_id = response.data["id"]
        
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "Quizzes", "weight_percent": "0.00", "sort_order": 2, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cat_quizzes_id = response.data["id"]
        
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "Homework", "weight_percent": "0.00", "sort_order": 3, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cat_homework_id = response.data["id"]
        
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "Projects", "weight_percent": "0.00", "sort_order": 4, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cat_projects_id = response.data["id"]
        
        # Step 2: Create assignments matching GradeEntry names
        self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/assignments/",
            {"name": "Final Exam", "category_id": cat_exams_id, "points_possible": "100.00", "is_published": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/assignments/",
            {"name": "Quiz 1", "category_id": cat_quizzes_id, "points_possible": "20.00", "is_published": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/assignments/",
            {"name": "Quiz 2", "category_id": cat_quizzes_id, "points_possible": "20.00", "is_published": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/assignments/",
            {"name": "Homework 1", "category_id": cat_homework_id, "points_possible": "10.00", "is_published": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/assignments/",
            {"name": "Project 1", "category_id": cat_projects_id, "points_possible": "50.00", "is_published": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        
        # Step 3: Use batch endpoint to set weights (40/30/20/10)
        response = self.client.put(
            f"/api/v1/academics/sections/{self.section_id}/categories/weights/",
            [
                {"id": cat_exams_id, "weight_percent": "40.00", "is_active": True},
                {"id": cat_quizzes_id, "weight_percent": "30.00", "is_active": True},
                {"id": cat_homework_id, "weight_percent": "20.00", "is_active": True},
                {"id": cat_projects_id, "weight_percent": "10.00", "is_active": True},
            ],
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 200, f"Batch weight update failed: {response.data}")
        
        # Step 4: Get transcript and verify weighted final_percent
        response = self.client.get(
            f"/api/v1/academics/transcript/{self.student_id}/",
            headers={"X-School-Id": self.school_id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Find the MATH-101 section in transcript
        section_data = None
        for term in response.data.get("terms", []):
            for course in term.get("courses", []):
                if course["section_id"] == self.section_id:
                    section_data = course
                    break
        
        self.assertIsNotNone(section_data, "Section not found in transcript")
        self.assertIsNotNone(section_data["final_percent"], "final_percent should not be null with weighted categories")
        self.assertAlmostEqual(
            section_data["final_percent"], 
            76.3, 
            places=1,
            msg="Weighted calculation: Exams 66%*40% + Quizzes 82.5%*30% + Homework 80%*20% + Projects 92%*10% = 76.3"
        )
    
    def test_null_when_mapping_broken(self):
        """Test that final_percent is null when assignment-to-category mapping is missing."""
        # Create categories with valid weights but NO assignments
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "TestCat", "weight_percent": "100.00", "sort_order": 1, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        
        # Get transcript - should have null final_percent (no assignments match GradeEntry names)
        response = self.client.get(
            f"/api/v1/academics/transcript/{self.student_id}/",
            headers={"X-School-Id": self.school_id}
        )
        self.assertEqual(response.status_code, 200)
        
        section_data = None
        for term in response.data.get("terms", []):
            for course in term.get("courses", []):
                if course["section_id"] == self.section_id:
                    section_data = course
                    break
        
        self.assertIsNotNone(section_data, "Section not found in transcript")
        self.assertIsNone(
            section_data["final_percent"], 
            "final_percent should be null when categories exist but no assignments match GradeEntry names"
        )
    
    def test_batch_endpoint_rejects_foreign_category_ids(self):
        """Test that batch endpoint rejects category IDs not belonging to the section."""
        # Create a category in this section
        response = self.client.post(
            f"/api/v1/academics/sections/{self.section_id}/categories/",
            {"name": "TestCat", "weight_percent": "0.00", "sort_order": 1, "is_active": True},
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        valid_cat_id = response.data["id"]
        
        # Try to batch update with a fake UUID (not in this section)
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.put(
            f"/api/v1/academics/sections/{self.section_id}/categories/weights/",
            [
                {"id": valid_cat_id, "weight_percent": "50.00", "is_active": True},
                {"id": fake_uuid, "weight_percent": "50.00", "is_active": True},
            ],
            headers={"X-School-Id": self.school_id},
            format="json"
        )
        
        # Should reject with validation error
        self.assertEqual(response.status_code, 400)
        error_message = str(response.data)
        self.assertIn("not found in this section", error_message.lower())
