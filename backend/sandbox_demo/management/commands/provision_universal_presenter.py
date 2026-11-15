"""Future owner-authorized existing-DEV activation. Never invokes migrations or Azure APIs."""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import RolePermission, School
from sandbox_demo.services import proof_metrics
from sandbox_demo.universal_runtime import require_hosted_presenter
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID
from sandbox_demo.universal_demo import _prepare_presenter
from sandbox_demo.universal_access import presenter_passwords
from sandbox_demo.universal_care import prepare_presenter_care
from sandbox_demo.universal_jireh import prepare_presenter_jireh
from sandbox_demo.universal_admissions import prepare_presenter_admissions


class Command(BaseCommand):
    help = "Preflight or explicitly create the owned fictional presenter in owner-enabled EXISTING DEV only."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--confirm-school-id")
        parser.add_argument("--enable-password-login", action="store_true")
        parser.add_argument("--archive-classroom", action="store_true")

    def handle(self, *args, **options):
        sha = options["expected_sha"]
        require_hosted_presenter(sha)
        if options["enable_password_login"] and not options["apply"]:
            raise CommandError("Credential initialization requires explicit --apply.")
        if options["apply"] and options["confirm_school_id"] != str(UNIVERSAL_SCHOOL_ID):
            raise CommandError("Explicit reserved presenter school confirmation required.")
        if options["archive_classroom"]:
            if not options["apply"] or options["enable_password_login"]:
                raise CommandError("Classroom archive requires --apply alone and retains credentials and audit history.")
            from sandbox_demo.universal_family import archive_presenter_classroom
            self.stdout.write(json.dumps({**archive_presenter_classroom(), "source_sha": sha}, sort_keys=True))
            return
        passwords = presenter_passwords() if options["enable_password_login"] else {}
        # Never install or broaden global role policy in a shared database.
        required = {"AID_DIRECTOR": ("financial_aid.view", "financial_aid.edit"),
            "REGISTRAR": ("admissions.view", "admissions.edit"),
            "HEAD_OF_SCHOOL": ("extended_care.view", "extended_care.edit", "summer_camp.view", "summer_camp.edit"),
            "DAYCARE_STAFF": ("diadem.daycare.view", "diadem.daycare.checkin", "diadem.daycare.release")}
        if not all(RolePermission.objects.filter(role_code=role, permission__code=code).exists()
                   for role, codes in required.items() for code in codes):
            raise CommandError("Existing approved permission catalog is incomplete; no grants were changed.")
        with transaction.atomic():
            require_hosted_presenter(sha)
            result = _prepare_presenter(apply=options["apply"], reset=False, passwords=passwords)
            if options["apply"]:
                result["care"] = prepare_presenter_care(apply=True)
                result["jireh"] = prepare_presenter_jireh(apply=True)
                result["admissions"] = prepare_presenter_admissions(apply=True)
                result.update(proof_metrics(School.objects.get(pk=UNIVERSAL_SCHOOL_ID)))
            result.update(source_sha=sha, release_certified=False)
        self.stdout.write(json.dumps(result, sort_keys=True))
