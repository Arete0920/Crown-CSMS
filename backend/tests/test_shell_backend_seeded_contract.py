import json

from django.test import TestCase

from crown_api.seeded_contract_probe import (
    get_seeded_contract_failures,
    get_seeded_contract_summary,
)


class ShellBackendSeededContractTests(TestCase):
    def test_canonical_shell_contract_returns_success_under_seeded_tenant_context(self):
        failures = get_seeded_contract_failures()
        summary = get_seeded_contract_summary()

        self.assertEqual(
            failures,
            [],
            msg=json.dumps(
                {
                    "summary": summary,
                    "failures": failures,
                },
                indent=2,
            ),
        )
