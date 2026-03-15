import json

from django.core.management.base import BaseCommand

from crown_api.write_contract_probe import (
    get_write_contract_failures,
    get_write_contract_summary,
    probe_write_contract,
)


class Command(BaseCommand):
    help = "Print shell/backend write mutation proof findings."

    def handle(self, *args, **options):
        summary = get_write_contract_summary()
        findings = probe_write_contract()
        failures = get_write_contract_failures()

        self.stdout.write("=== SHELL BACKEND WRITE PROOF SUMMARY ===")
        self.stdout.write(json.dumps(summary, indent=2))
        self.stdout.write("")

        self.stdout.write("=== WRITE PROBE FINDINGS ===")
        self.stdout.write(json.dumps(findings, indent=2))
        self.stdout.write("")

        if failures:
            self.stdout.write(self.style.ERROR("=== FAILURES ==="))
            self.stdout.write(json.dumps(failures, indent=2))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS("No write contract failures found."))
