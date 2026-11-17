import json
from django.core.management.base import BaseCommand
from sandbox_demo.universal_reset import rollover_presenter


class Command(BaseCommand):
    help = "Preflight or explicitly roll the owned presenter to a new bounded generation, retaining all historical records."

    def add_arguments(self, parser):
        parser.add_argument("--expected-current-school-id", required=True)
        parser.add_argument("--request-key", required=True)
        parser.add_argument("--expected-sha")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--enable-password-login", action="store_true")

    def handle(self, *args, **options):
        from django.conf import settings
        from django.core.management.base import CommandError
        if getattr(settings, "CROWN_ENV", "") != "local":
            if not options["expected_sha"]:
                raise CommandError("Hosted rollover requires an explicit approved source revision.")
            from sandbox_demo.universal_runtime import require_hosted_presenter
            require_hosted_presenter(options["expected_sha"])
        self.stdout.write(json.dumps(rollover_presenter(expected_current=options["expected_current_school_id"],
            request_key=options["request_key"], apply=options["apply"],
            enable_password_login=options["enable_password_login"]), sort_keys=True))
