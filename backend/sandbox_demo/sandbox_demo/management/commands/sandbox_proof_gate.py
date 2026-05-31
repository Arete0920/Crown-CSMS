from django.core.management.base import BaseCommand, CommandError

from sandbox_demo.services import assert_flagship_proof


class Command(BaseCommand):
    help = "Run the CROWN flagship sandbox proof gate."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Fail if any proof row is not PASS.")

    def handle(self, *args, **opts):
        findings = assert_flagship_proof()
        failures = []

        for finding in findings:
            level = finding["level"]
            message = finding["message"]
            if level == "PASS":
                self.stdout.write(self.style.SUCCESS(f"PASS {message}"))
            else:
                failures.append(finding)
                self.stdout.write(self.style.ERROR(f"FAIL {message}"))

        if opts.get("strict") and failures:
            raise CommandError(f"Sandbox proof gate failed: {len(failures)} failure(s).")

        self.stdout.write(self.style.SUCCESS(f"Sandbox proof gate complete: pass={len(findings)-len(failures)} fail={len(failures)}"))
