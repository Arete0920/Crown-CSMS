"""School-authorized Kairos standalone CSV preview/export Django tests."""
from django.test import TestCase
from section_scheduler_wizard.models import SectionPlacement
from section_scheduler_wizard.canonical_snapshot import build_canonical_planning_snapshot
from .test_views import BASE, _client_for, _fixtures, _headers

IMPORT = BASE + "standalone/import-preview/"
EXPORT = BASE + "standalone/export-preview/"


class KairosStandaloneApiTests(TestCase):
    def setUp(self):
        self.school, self.year, self.section, self.template, self.block, self.room = _fixtures()
        self.client = _client_for(self.school)
        self.actor = self.client.handler._force_user
        # Standalone export is intentionally fail-closed for sections with no
        # verified teacher. Mirror the canonical assignment used in preview.
        from academics.models import TeacherAssignment
        from core.models import Staff
        self.staff = Staff.objects.create(
            school=self.school, first_name="Synthetic", last_name="Teacher",
            email="kairos-standalone@example.invalid",
            role_type="TEACHER", status="ACTIVE",
        )
        TeacherAssignment.objects.create(
            school_id=self.school.id, section=self.section, staff=self.staff,
        )

    def base(self):
        snapshot = build_canonical_planning_snapshot(
            actor=self.actor, school_id=self.school.id,
            academic_year_id=self.year.id, term_code="S1",
        )
        return dict(
            academic_year_id=str(self.year.id), term_code="S1",
            expected_source_fingerprint=snapshot.source_fingerprint,
        )

    def placements(self):
        return [{"section_id":str(self.section.id),
                 "period_id":str(self.block.id), "room_id":str(self.room.id)}]

    def test_roundtrip_is_valid_preview_and_never_publishes(self):
        before = SectionPlacement.objects.count()
        data = self.base()
        data["placements"] = self.placements()
        exported = self.client.post(EXPORT, data, format="json", **_headers(self.school))
        self.assertEqual(exported.status_code, 200, exported.data)
        self.assertFalse(exported.data["publication_allowed"])
        self.assertIn("no-store", exported["Cache-Control"])
        source = exported.data["csv_text"]
        self.assertNotIn("student_name", source.lower())
        input_data = self.base()
        input_data["csv_text"] = source
        imported = self.client.post(IMPORT, input_data, format="json", **_headers(self.school))
        self.assertEqual(imported.status_code, 200, imported.data)
        self.assertEqual(imported.data["status"], "VALID_PREVIEW_ONLY")
        self.assertEqual(imported.data["placements"], self.placements())
        self.assertFalse(imported.data["publication_allowed"])
        self.assertEqual(SectionPlacement.objects.count(), before)

    def test_stale_fingerprint_rejected(self):
        data = self.base()
        data["expected_source_fingerprint"] = "b" * 64
        data["csv_text"] = "section_id,period_id,room_id\n"
        res = self.client.post(IMPORT, data, format="json", **_headers(self.school))
        self.assertEqual(res.status_code, 409)
        self.assertFalse(res.data["publication_allowed"])

    def test_malformed_csv_refused(self):
        data = self.base()
        data["csv_text"] = "section_id,period_id,room_id\nforeign,p1,r1\n"
        res = self.client.post(IMPORT, data, format="json", **_headers(self.school))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(SectionPlacement.objects.count(), 0)

    def test_role_revocation_blocks_both_endpoints(self):
        from core.models import UserRole
        data = self.base()
        UserRole.objects.filter(user=self.actor,school=self.school).delete()
        data["csv_text"] = "section_id,period_id,room_id\n"
        a = self.client.post(IMPORT, data, format="json", **_headers(self.school))
        data.pop("csv_text")
        data["placements"] = self.placements()
        b = self.client.post(EXPORT, data, format="json", **_headers(self.school))
        self.assertEqual(a.status_code, 403)
        self.assertEqual(b.status_code, 403)
        self.assertEqual(SectionPlacement.objects.count(), 0)
