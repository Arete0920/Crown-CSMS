"""Local fictional partner seed must be gated, isolated, repeatable and off-repo."""
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from jireh_sgo.models import ( SGOApplication, SGOAuditEvent, SGOAward, SGOFamilyGrant, SGOFamilyIntake, SGOMembership, SGOOrganization, SGOProcessorAssignment, SGOProgram, )
from crown_api.management.commands.seed_fictional_sgo_intake import HERITAGE_SCHOOL
@override_settings( CROWN_ENV="local", DJANGO_ENV="local", DEBUG=True, CROWN_DEMO_MODE=False, CROWN_SGO_FICTIONAL_INTAKE_ENABLED=True, )
class FictionalSGOLocalSeedTests(TestCase):
    def setUp(self):
        if connection.vendor != "sqlite":
            self.skipTest("Fictional SGO seed is restricted to isolated SQLite.")
    @patch("crown_api.management.commands.seed_fictional_sgo_intake._require_isolated_local_database")
    def test_two_partner_programs_separate_grants_and_repeatable_local_credentials(self, guard):
        # This unit test uses Django's disposable test SQLite database, not
        # the exact on-disk Heritage path checked by the real command.
        self.assertIsNotNone(guard)
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sgo-credentials.txt"
            call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            self.assertTrue(target.is_file())
            for model in (SGOOrganization, SGOProgram, SGOFamilyGrant, SGOProcessorAssignment, SGOMembership):
                self.assertEqual(model.objects.count(), 2)
            # The parent seeder intentionally creates one Heritage-linked inventory
            # application per partner; these are NOT submitted family intakes.
            self.assertEqual(SGOApplication.objects.count(), 2)
            self.assertEqual(
                SGOApplication.objects.filter(school_key=HERITAGE_SCHOOL).count(), 2
            )
            # Fixed UUIDs identify admin-created inventory only. No family
            # consent or submission exists until an authenticated family POST.
            inventory_students = {
                uuid5(NAMESPACE_URL, f"crown-fictional-sgo-{code}-inventory")
                for code in ("de", "pa")
            }
            self.assertEqual(
                set(SGOApplication.objects.values_list("student_key", flat=True)),
                inventory_students,
            )
            self.assertFalse(SGOFamilyIntake.objects.exists())
            self.assertEqual(
                SGOAuditEvent.objects.filter(action=SGOAuditEvent.APPLICATION_CREATED).count(), 2
            )
            self.assertFalse(SGOAuditEvent.objects.filter(action=SGOAuditEvent.INTAKE_SUBMITTED).exists())
            self.assertFalse(SGOAward.objects.exists())
            self.assertFalse(SGOApplication.objects.filter(student_key__in=SGOFamilyGrant.objects.values("student_key")).exists())
            first = target.read_text(encoding="utf-8")
            self.assertIn("sgo_demo_de_family", first)
            self.assertIn("sgo_demo_pa_processor", first)
            self.assertIn("Fictional Delaware SGO", first)
            self.assertIn("Fictional Pennsylvania SGO", first)
            User = get_user_model()
            family_a = User.objects.get(username="sgo_demo_de_family")
            family_b = User.objects.get(username="sgo_demo_pa_family")
            self.assertNotEqual(family_a.id, family_b.id)
            program_a = SGOFamilyGrant.objects.get(user=family_a).program
            program_b = SGOFamilyGrant.objects.get(user=family_b).program
            self.assertNotEqual(program_a.organization_id, program_b.organization_id)
            self.assertFalse(SGOMembership.objects.filter(user=family_a).exists())
            self.assertFalse(SGOMembership.objects.filter(user=family_b).exists())
            self.assertFalse(SGOProcessorAssignment.objects.filter(user=family_a).exists())
            call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            for model in (SGOOrganization, SGOProgram, SGOFamilyGrant, SGOProcessorAssignment, SGOMembership):
                self.assertEqual(model.objects.count(), 2)
            self.assertFalse(SGOAward.objects.exists())
            self.assertEqual(SGOApplication.objects.count(), 2)
            self.assertFalse(SGOFamilyIntake.objects.exists())
            self.assertEqual(
                SGOAuditEvent.objects.filter(action=SGOAuditEvent.APPLICATION_CREATED).count(), 2
            )
            self.assertFalse(SGOApplication.objects.filter(
                student_key__in=SGOFamilyGrant.objects.values("student_key")
            ).exists())
            self.assertNotEqual(target.read_text(encoding="utf-8"), first)
            self.assertEqual(guard.call_count, 2)
    @patch("crown_api.management.commands.seed_fictional_sgo_intake._require_isolated_local_database")
    def test_seed_never_reactivates_revoked_partner_or_grants(self, guard):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "credentials.txt"
            call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            for model in (SGOOrganization, SGOMembership, SGOFamilyGrant, SGOProcessorAssignment):
                with self.subTest(model=model.__name__):
                    record = model.objects.order_by("pk").first()
                    record.active = False
                    record.save(update_fields=["active"])
                    original = target.read_bytes()
                    with self.assertRaisesRegex(CommandError, "manual reconciliation"):
                        call_command("seed_fictional_sgo_intake", credentials_file=str(target))
                    record.refresh_from_db()
                    self.assertFalse(record.active)
                    self.assertEqual(target.read_bytes(), original)
                    self.assertEqual(model.objects.count(), 2)
                    record.active = True
                    record.save(update_fields=["active"])
    def test_local_mode_alone_cannot_seed_a_non_heritage_database(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sgo-credentials.txt"
            with self.assertRaisesRegex(CommandError, "isolated Heritage local SQLite"):
                call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            self.assertFalse(target.exists())
            self.assertFalse(SGOOrganization.objects.exists())
            self.assertFalse(get_user_model().objects.filter( username__startswith="sgo_demo_", ).exists())
    @patch("crown_api.management.commands.seed_fictional_sgo_intake._require_isolated_local_database")
    def test_seeded_credentials_obtain_jwt_and_scope_family_processor(self, guard):
        """Exercise the real SimpleJWT route, not force_authenticate or mocked login."""
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "accounts.txt"
            call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            lines = target.read_text(encoding="utf-8").splitlines()
            def accounts(label):
                return [line.split(": ", 1)[1].split(" / ", 1)
                        for line in lines if line.startswith(label + ": ")]
            families, processors, partners = (accounts("Family login"),
                                              accounts("Processor login"),
                                              accounts("Partner SGO admin (no automatic processor rights)"))
            self.assertEqual((len(families), len(processors), len(partners)), (2, 2, 2))
            def signed_client(pair):
                client = APIClient()
                token = client.post("/api/v1/auth/token/",
                                    {"username": pair[0], "password": pair[1]},
                                    format="json")
                self.assertEqual(token.status_code, 200, token.data)
                self.assertTrue(token.data.get("access"))
                client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
                return client

            delaware = signed_client(families[0])
            programs = delaware.get("/api/v1/jireh-sgo/family/programs/")
            self.assertEqual(programs.status_code, 200, programs.data)
            self.assertEqual(len(programs.data["programs"]), 1)
            selected = programs.data["programs"][0]
            self.assertIsNone(selected["application_id"])
            submitted = delaware.post("/api/v1/jireh-sgo/family/submit/", {
                "program_id": selected["id"], "grade_level": "K",
                "consent": True, "consent_version": selected["consent_version"],
                "submission_key": str(uuid4()),
            }, format="json")
            self.assertEqual(submitted.status_code, 201, submitted.data)
            application_id = submitted.data["application"]["id"]
            self.assertEqual(delaware.get(
                f"/api/v1/jireh-sgo/family/applications/{application_id}/"
            ).status_code, 200)
            # Two synthetic inventory rows remain separate from the one
            # authorized family submission, without creating a grantor award.
            self.assertEqual(SGOApplication.objects.count(), 3)
            self.assertEqual(SGOFamilyIntake.objects.count(), 1)
            intake = SGOFamilyIntake.objects.select_related(
                "application", "grant__user"
            ).get(application_id=application_id)
            self.assertEqual(intake.status, SGOFamilyIntake.SUBMITTED)
            self.assertEqual(intake.grant.user.username, families[0][0])
            self.assertEqual(intake.application.program_id, intake.grant.program_id)
            self.assertEqual(intake.application.student_key, intake.grant.student_key)
            self.assertEqual(intake.application.school_key, intake.grant.school_key)
            self.assertEqual(
                SGOAuditEvent.objects.filter(
                    action=SGOAuditEvent.INTAKE_SUBMITTED,
                    subject_key=application_id,
                    actor__username=families[0][0],
                ).count(), 1
            )
            self.assertFalse(SGOAward.objects.exists())

            pennsylvania = signed_client(families[1])
            self.assertEqual(pennsylvania.get(
                f"/api/v1/jireh-sgo/family/applications/{application_id}/"
            ).status_code, 403)
            self.assertEqual(len(pennsylvania.get(
                "/api/v1/jireh-sgo/family/programs/"
            ).data["programs"]), 1)
            processor = signed_client(processors[0])
            queue = processor.get(
                f"/api/v1/jireh-sgo/processor/programs/{selected['id']}/queue/"
            )
            self.assertEqual(queue.status_code, 200)
            self.assertEqual([row["id"] for row in queue.data["applications"]],
                             [application_id])
            correction = processor.post(
                f"/api/v1/jireh-sgo/processor/applications/{application_id}/request-correction/",
                {"expected_revision": 1, "reason": "GRADE_UNVERIFIED",
                 "request_key": str(uuid4())}, format="json",
            )
            self.assertEqual(correction.status_code, 200, correction.data)
            self.assertEqual(correction.data["application"]["status"], "CORRECTION_REQUESTED")
            pending = delaware.get(
                f"/api/v1/jireh-sgo/family/applications/{application_id}/"
            )
            self.assertEqual(pending.status_code, 200, pending.data)
            self.assertEqual(pending.data["application"]["revision"], 2)
            amended = delaware.post(
                f"/api/v1/jireh-sgo/family/applications/{application_id}/correct/",
                {"expected_revision": 2, "grade_level": "2",
                 "correction_key": str(uuid4())}, format="json",
            )
            self.assertEqual(amended.status_code, 200, amended.data)
            self.assertEqual(amended.data["application"]["status"], "RESUBMITTED")
            persisted = delaware.get(
                f"/api/v1/jireh-sgo/family/applications/{application_id}/"
            )
            self.assertEqual(persisted.status_code, 200, persisted.data)
            self.assertEqual((persisted.data["application"]["revision"],
                              persisted.data["application"]["grade_level"]), (3, "2"))
            self.assertFalse(SGOAward.objects.exists())
            partner = signed_client(partners[0])
            self.assertEqual(partner.get(
                "/api/v1/jireh-sgo/family/programs/"
            ).data["programs"], [])
            self.assertEqual(partner.get(
                f"/api/v1/jireh-sgo/processor/programs/{selected['id']}/queue/"
            ).status_code, 403)
            self.assertEqual(guard.call_count, 1)

    def test_hosted_and_disabled_seed_fail_closed_without_side_effects(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sgo-credentials.txt"
            for overrides in ( {"CROWN_SGO_FICTIONAL_INTAKE_ENABLED": False}, {"CROWN_ENV": "production"}, {"DJANGO_ENV": "staging"}, {"DEBUG": False}, {"CROWN_DEMO_MODE": True}, ):
                with self.subTest(overrides=overrides), override_settings(**overrides):
                    with self.assertRaises(CommandError):
                        call_command("seed_fictional_sgo_intake", credentials_file=str(target))
                    self.assertFalse(target.exists())
                    self.assertFalse(SGOOrganization.objects.exists())
