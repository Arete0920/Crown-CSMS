import unittest
from prepare_dev_certification_tenants import validate_target


class TargetBoundaryTests(unittest.TestCase):
    def test_accepts_only_authorized_dev_postgresql(self):
        validate_target("dev", "postgresql", "postgresql://synthetic@crown-pg-dev.postgres.database.azure.com/crown")

    def test_rejects_other_environments_databases_and_lookalike_hosts(self):
        cases = [
            ("production", "postgresql", "postgresql://synthetic@crown-pg-dev.postgres.database.azure.com/crown"),
            ("dev", "sqlite", "sqlite:///test.db"),
            ("dev", "postgresql", "postgresql://synthetic@crown-pg-prod.postgres.database.azure.com/crown"),
            ("dev", "postgresql", "postgresql://synthetic@crown-pg-dev.postgres.database.azure.com.attacker.invalid/crown"),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_target(*case)


if __name__ == "__main__":
    unittest.main()
