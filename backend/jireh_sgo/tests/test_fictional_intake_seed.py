"""Local fictional partner seed must be gated, isolated, repeatable and off-repo."""
from pathlib import Path
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from jireh_sgo.models import ( SGOApplication, SGOFamilyGrant, SGOMembership, SGOOrganization, SGOProcessorAssignment, SGOProgram, )
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
            self.assertEqual(SGOOrganization.objects.count(), 2)
            self.assertEqual(SGOProgram.objects.count(), 2)
            self.assertEqual(SGOFamilyGrant.objects.count(), 2)
            self.assertEqual(SGOProcessorAssignment.objects.count(), 2)
            self.assertEqual(SGOMembership.objects.count(), 2)
            self.assertEqual(SGOApplication.objects.count(), 0)
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
            self.assertEqual(SGOOrganization.objects.count(), 2)
            self.assertEqual(SGOProgram.objects.count(), 2)
            self.assertEqual(SGOFamilyGrant.objects.count(), 2)
            self.assertEqual(SGOProcessorAssignment.objects.count(), 2)
            self.assertEqual(SGOMembership.objects.count(), 2)
            self.assertNotEqual(target.read_text(encoding="utf-8"), first)
            self.assertEqual(guard.call_count, 2)
    def test_local_mode_alone_cannot_seed_a_non_heritage_database(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sgo-credentials.txt"
            with self.assertRaisesRegex(CommandError, "isolated Heritage local SQLite"):
                call_command("seed_fictional_sgo_intake", credentials_file=str(target))
            self.assertFalse(target.exists())
            self.assertFalse(SGOOrganization.objects.exists())
            self.assertFalse(get_user_model().objects.filter( username__startswith="sgo_demo_", ).exists())
    def test_hosted_and_disabled_seed_fail_closed_without_side_effects(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "sgo-credentials.txt"
            for overrides in ( {"CROWN_SGO_FICTIONAL_INTAKE_ENABLED": False}, {"CROWN_ENV": "production"}, {"DJANGO_ENV": "staging"}, {"DEBUG": False}, {"CROWN_DEMO_MODE": True}, ):
                with self.subTest(overrides=overrides), override_settings(**overrides):
                    with self.assertRaises(CommandError):
                        call_command("seed_fictional_sgo_intake", credentials_file=str(target))
                    self.assertFalse(target.exists())
                    self.assertFalse(SGOOrganization.objects.exists())
