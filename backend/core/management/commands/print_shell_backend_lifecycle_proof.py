import json

from django.core.management.base import BaseCommand

from crown_api.lifecycle_contract_probe import (
    get_lifecycle_contract_failures,
    get_lifecycle_contract_summary,
    probe_lifecycle_contract,
)


class Command(BaseCommand):
    help = "Print shell/backend lifecycle read-back proof findings."

    def handle(self, *args, **options):
        summary = get_lifecycle_contract_summary()
        findings = probe_lifecycle_contract()
        failures = get_lifecycle_contract_failures()

        self.stdout.write("=== SHELL BACKEND LIFECYCLE PROOF SUMMARY ===")
        self.stdout.write(json.dumps(summary, indent=2))
        self.stdout.write("")

        self.stdout.write("=== LIFECYCLE PROBE FINDINGS ===")
        self.stdout.write(json.dumps(findings, indent=2))
        self.stdout.write("")

        if failures:
            self.stdout.write(self.style.ERROR("=== FAILURES ==="))
            self.stdout.write(json.dumps(failures, indent=2))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("No lifecycle contract failures found."))
