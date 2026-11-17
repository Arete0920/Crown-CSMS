import json

from django.core.management.base import BaseCommand, CommandError
from sandbox_demo.universal_demo import prepare_presenter


class Command(BaseCommand):
    help = "Preflight or explicitly create/reset the isolated LOCAL fictional presenter foundation."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--archive-classroom", action="store_true",
                            help="Reset visible practice work and retain submission/grade history; requires --apply.")
        parser.add_argument("--enable-password-login", action="store_true",
                            help="Initialize new fictional accounts with distinct operator secrets from environment variables.")

    def handle(self, *args, **options):
        from sandbox_demo.universal_demo import require_local_presenter
        require_local_presenter()
        if options["archive_classroom"]:
            if not options["apply"] or options["reset"] or options["enable_password_login"]:
                raise CommandError("Classroom archive requires --apply alone; credentials and school records are preserved.")
            from sandbox_demo.universal_family import archive_presenter_classroom
            self.stdout.write(json.dumps(archive_presenter_classroom(), sort_keys=True))
            return
        self.stdout.write(json.dumps(prepare_presenter(
            apply=options["apply"], reset=options["reset"],
            enable_password_login=options["enable_password_login"],
        ), sort_keys=True))
