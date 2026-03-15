import json

from django.core.management.base import BaseCommand

from crown_api.seeded_contract_probe import (
    get_seeded_contract_failures,
    get_seeded_contract_summary,
    probe_seeded_contract,
)


class Command(BaseCommand):
    help = "Print seeded tenant shell/backend proof findings."

    def handle(self, *args, **options):
        summary = get_seeded_contract_summary()
        findings = probe_seeded_contract()
        failures = get_seeded_contract_failures()

        self.stdout.write("=== SEEDED TENANT SHELL BACKEND PROOF SUMMARY ===")
        self.stdout.write(json.dumps(summary, indent=2))
        self.stdout.write("")

        self.stdout.write("=== SEEDED PROBE FINDINGS ===")
        self.stdout.write(json.dumps(findings, indent=2))
        self.stdout.write("")

        if failures:
            self.stdout.write(self.style.ERROR("=== FAILURES ==="))
            self.stdout.write(json.dumps(failures, indent=2))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("No seeded tenant contract failures found."))
