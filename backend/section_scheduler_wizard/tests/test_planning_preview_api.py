"""Authenticated Kairos preview API regression suite using canonical synthetic records."""
from django.test import TestCase

from academics.models import Course, Section, TeacherAssignment
from core.models import Staff
from room_setup_wizard.models import Room
from section_scheduler_wizard.canonical_snapshot import build_canonical_planning_snapshot
from section_scheduler_wizard.models import SectionPlacement
from .test_views import BASE, _client_for, _configured_session, _fixtures, _headers

ENDPOINT = BASE + "preview/"


class KairosIntegratedPreviewTests(TestCase):
    def setUp(self):
        self.school, self.year, self.section, self.template, self.block, self.room = _fixtures()
        self.client = _client_for(self.school)
        self.actor = self.client.handler._force_user
        self.staff = Staff.objects.create(
            school=self.school, first_name="Synthetic", last_name="Teacher",
            email="kairos-preview@example.invalid", role_type="TEACHER", status="ACTIVE",
        )
        TeacherAssignment.objects.create(school_id=self.school.id, section=self.section, staff=self.staff)

    def snapshot(self):
        return build_canonical_planning_snapshot(
            actor=self.actor, school_id=self.school.id,
            academic_year_id=self.year.id, term_code="S1",
        )

    def body(self):
        snap = self.snapshot()
        return {
            "academic_year_id": str(self.year.id),
            "term_code": "S1",
            "expected_source_fingerprint": snap.source_fingerprint,
            "candidate_domains": {
                str(self.section.id): [
                    {"period_id": str(self.block.id), "room_id": str(self.room.id)}
                ],
            },
            "teacher_rules": [{
                "staff_id": str(self.staff.id),
                "unavailable_period_ids": [],
                "max_instructional_minutes_per_cycle": 240,
                "minimum_preparation_minutes_per_cycle": 0,
            }],
            "template_occurrences": {str(self.template.id): 1},
            "node_limit": 40,
        }

    def post(self, data, client=None, school=None):
        client = client or self.client
        return client.post(
            ENDPOINT, data, format="json",
            **_headers(school or self.school),
        )

    def add_second_section(self):
        from datetime import time
        from bell_schedule_wizard.models import PeriodBlock
        course = Course.objects.create(
            school_id=self.school.id, code="MATH2",
            name="Mathematics 2", department="Math", credits="1.00",
        )
        other = Section.objects.create(
            school_id=self.school.id, course=course, term_ref=self.section.term_ref,
            term="S1", teacher_name="", grade_band="9",
        )
        TeacherAssignment.objects.create(
            school_id=self.school.id, section=other, staff=self.staff,
        )
        later = PeriodBlock.objects.create(
            template=self.template, code="P2", label="Period 2",
            start_time=time(9, 0), end_time=time(10, 0),
            ordering=1, is_instructional=True,
        )
        return other, later

    def test_authenticated_canonical_preview_is_read_only(self):
        data = self.body()
        before = SectionPlacement.objects.count()
        res = self.post(data)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["status"], "FEASIBLE")
        self.assertFalse(res.data["publication_allowed"])
        self.assertEqual(res.data["authority"], "PROVISIONAL_INPUT_ASSUMPTIONS")
        self.assertEqual(len(res.data["preview_digest"]), 64)
        self.assertEqual(res.data["source_fingerprint"], data["expected_source_fingerprint"])
        self.assertEqual(SectionPlacement.objects.count(), before)
        self.assertEqual(self.post(data).data["preview_digest"], res.data["preview_digest"])

    def test_unauthorized_role_cannot_preview(self):
        unauth = _client_for(self.school, role=None)
        self.assertEqual(self.post(self.body(), client=unauth).status_code, 403)

    def test_missing_or_outdated_snapshot_proof_denied(self):
        body = self.body()
        body["expected_source_fingerprint"] = "0" * 64
        res = self.post(body)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.data["error"], "STALE_SOURCE")
        self.assertFalse(res.data["publication_allowed"])
        body.pop("expected_source_fingerprint")
        self.assertEqual(self.post(body).status_code, 400)

    def test_missing_teacher_policy_refused(self):
        body = self.body()
        body["teacher_rules"] = []
        self.assertEqual(self.post(body).status_code, 400)

    def test_foreign_staff_rule_refused(self):
        body = self.body()
        body["teacher_rules"][0]["staff_id"] = "forged"
        self.assertEqual(self.post(body).status_code, 400)

    def test_unknown_period_is_refused(self):
        body = self.body()
        body["candidate_domains"][str(self.section.id)][0]["period_id"] = "forged"
        self.assertEqual(self.post(body).status_code, 400)

    def test_foreign_section_is_refused(self):
        body = self.body()
        body["candidate_domains"] = {"forged": body["candidate_domains"][str(self.section.id)]}
        self.assertEqual(self.post(body).status_code, 400)

    def test_unverified_student_links_fail_closed(self):
        from households.models import Household, Student as CompatibilityStudent
        from academics.models import Enrollment
        household = Household.objects.create(school_id=self.school.id, name="Synthetic")
        other = CompatibilityStudent.objects.create(
            school_id=self.school.id, household=household,
            first_name="Synthetic", last_name="Student",
        )
        Enrollment.objects.create(
            school_id=self.school.id, section=self.section, student=other,
        )
        data = {
            "academic_year_id": str(self.year.id),
            "term_code": "S1",
            "expected_source_fingerprint": "a" * 64,
        }
        self.assertEqual(self.post(data).status_code, 400)
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_budget_exhaustion_is_not_infeasibility(self):
        second, later = self.add_second_section()
        body = self.body()
        body["candidate_domains"][str(second.id)] = [
            {"period_id": str(self.block.id), "room_id": str(self.room.id)},
            {"period_id": str(later.id), "room_id": str(self.room.id)},
        ]
        body["node_limit"] = 1
        res = self.post(body)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["status"], "UNKNOWN")
        self.assertEqual(res.data["placements"], [])
        self.assertFalse(res.data["publication_allowed"])
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_infeasible_teacher_policy_no_publish(self):
        data = self.body()
        data["teacher_rules"][0]["max_instructional_minutes_per_cycle"] = 0
        res = self.post(data)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["status"], "INFEASIBLE")
        self.assertEqual(res.data["placements"], [])
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_authorized_options_supply_only_opaque_canonical_ids(self):
        result = self.client.get(
            ENDPOINT + "options/",
            {"academic_year_id": str(self.year.id), "term_code": "S1"},
            **_headers(self.school),
        )
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["source_fingerprint"], self.body()["expected_source_fingerprint"])
        self.assertEqual(result.data["section_ids"], [str(self.section.id)])
        self.assertEqual(result.data["assigned_staff_ids"], [str(self.staff.id)])
        self.assertFalse(result.data["publication_allowed"])
        self.assertNotIn("student_ids", result.data)
        self.assertNotIn("student_name", str(result.data).lower())
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_options_cannot_access_without_school_grant(self):
        unauth = _client_for(self.school, role=None)
        result = unauth.get(
            ENDPOINT + "options/",
            {"academic_year_id": str(self.year.id), "term_code": "S1"},
            **_headers(self.school),
        )
        self.assertEqual(result.status_code, 403)

    def test_options_reject_foreign_year(self):
        from core.models import AcademicYear
        from datetime import date
        foreign_school, *_ = _fixtures()
        foreign_year = AcademicYear.objects.filter(school=foreign_school).first()
        response = self.client.get(
            ENDPOINT + "options/",
            {"academic_year_id": str(foreign_year.id), "term_code": "S1"},
            **_headers(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_generated_preview_requires_explicit_manual_publication_and_supports_undo(self):
        # This exercises the complete existing governed write/verify/undo path.
        # The preview endpoint itself must remain entirely read-only.
        proposal = self.post(self.body())
        self.assertEqual(proposal.status_code, 200, proposal.data)
        self.assertEqual(proposal.data["status"], "FEASIBLE")
        self.assertFalse(proposal.data["publication_allowed"])
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(), 0)

        session_id = _configured_session(self.client, self.school, self.year)
        rows = [{
            "section_id": p["section_id"],
            "day_template_id": str(self.template.id),
            "period_block_id": p["period_id"],
            "room_id": p["room_id"],
        } for p in proposal.data["placements"]]
        stage = self.client.post(
            f"{BASE}{session_id}/sections/",
            {"sections": rows}, format="json", **_headers(self.school),
        )
        self.assertEqual(stage.status_code, 200, stage.data)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(), 0)

        publish = self.client.post(
            f"{BASE}{session_id}/commit/", {"confirm": True},
            format="json", **_headers(self.school),
        )
        self.assertEqual(publish.status_code, 200, publish.data)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(), 1)
        verified = self.client.get(
            f"{BASE}{session_id}/verify/", **_headers(self.school),
        )
        self.assertEqual(verified.status_code, 200, verified.data)
        undone = self.client.post(
            f"{BASE}{session_id}/undo/", {"confirm": True},
            format="json", **_headers(self.school),
        )
        self.assertEqual(undone.status_code, 200, undone.data)
        self.assertEqual(SectionPlacement.objects.filter(is_active=True).count(), 0)

    def test_source_changes_during_search_return_stale_not_feasible(self):
        from dataclasses import replace
        from unittest.mock import patch
        original = self.snapshot()
        changed = replace(original, source_fingerprint="b" * 64)
        data = self.body()
        with patch(
            "section_scheduler_wizard.planning_preview_api.build_canonical_planning_snapshot",
            side_effect=[original, changed],
        ):
            result = self.post(data)
        self.assertEqual(result.status_code, 409, result.data)
        self.assertEqual(result.data["error"], "SOURCE_CHANGED_DURING_PREVIEW")
        self.assertFalse(result.data["publication_allowed"])
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_cross_school_principal_cannot_read_or_execute_preview(self):
        foreign_school, *_ = _fixtures()
        foreign_client = _client_for(foreign_school)
        response = self.post(self.body(), client=foreign_client)
        self.assertEqual(response.status_code, 403)
        options = foreign_client.get(
            ENDPOINT + "options/",
            {"academic_year_id": str(self.year.id), "term_code": "S1"},
            **_headers(self.school),
        )
        self.assertEqual(options.status_code, 403)
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_excessive_synchronous_search_budget_is_denied(self):
        data = self.body()
        data["node_limit"] = 2501
        response = self.post(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SectionPlacement.objects.count(), 0)
