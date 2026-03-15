import json

from django.test import TestCase

from crown_api.lifecycle_contract_probe import (
    get_lifecycle_contract_failures,
    get_lifecycle_contract_summary,
)


class ShellBackendLifecycleContractTests(TestCase):
    def test_canonical_shell_contract_persists_and_reads_back_after_write(self):
        failures = get_lifecycle_contract_failures()
        summary = get_lifecycle_contract_summary()

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
