import json

from django.test import TestCase

from crown_api.write_contract_probe import (
    get_write_contract_failures,
    get_write_contract_summary,
)


class ShellBackendWriteContractTests(TestCase):
    def test_canonical_shell_contract_accepts_real_write_mutations(self):
        failures = get_write_contract_failures()
        summary = get_write_contract_summary()

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
