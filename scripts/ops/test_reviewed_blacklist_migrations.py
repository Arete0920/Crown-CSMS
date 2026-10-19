"""No-database tests for the reviewed SimpleJWT migration allowlist."""
import unittest
from types import SimpleNamespace

import reviewed_blacklist_migrations as subject


class BlacklistMigrationBoundaryTests(unittest.TestCase):
    def test_clean_uninitialized_database(self):
        self.assertTrue(subject.validate_source_state(
            runtime_version="5.5.1",
            disk_names=subject.MIGRATION_NAMES,
            applied_names=(),
            table_names=set(),
        ))

    def test_canonical_partial_and_complete_history(self):
        for count in range(1, len(subject.MIGRATION_NAMES) + 1):
            with self.subTest(count=count):
                self.assertTrue(subject.validate_source_state(
                    runtime_version="5.5.1",
                    disk_names=subject.MIGRATION_NAMES,
                    applied_names=subject.MIGRATION_NAMES[:count],
                    table_names={subject.OUTSTANDING_TABLE, subject.BLACKLISTED_TABLE},
                ))

    def test_reject_unknown_migration_and_fabricated_0013(self):
        for extra in ("0013_blacklist", "0014_unsafe_local"):
            with self.subTest(extra=extra), self.assertRaises(subject.BlacklistBoundaryError):
                subject.validate_source_state(
                    runtime_version="5.5.1",
                    disk_names=(*subject.MIGRATION_NAMES, extra),
                    applied_names=(),
                    table_names=set(),
                )

    def test_reject_noncanonical_applied_history(self):
        cases = [
            ("0013_blacklist",),
            (subject.MIGRATION_NAMES[-1],),
            (subject.MIGRATION_NAMES[0], subject.MIGRATION_NAMES[2]),
        ]
        for applied in cases:
            with self.subTest(applied=applied), self.assertRaises(subject.BlacklistBoundaryError):
                subject.validate_source_state(
                    runtime_version="5.5.1",
                    disk_names=subject.MIGRATION_NAMES,
                    applied_names=applied,
                    table_names={subject.OUTSTANDING_TABLE, subject.BLACKLISTED_TABLE},
                )

    def test_reject_version_and_schema_drift(self):
        variants = [
            {"runtime_version": "5.3.1"},
            {"table_names": {subject.OUTSTANDING_TABLE}},
            {"table_names": set()},
        ]
        defaults = dict(
            runtime_version="5.5.1",
            disk_names=subject.MIGRATION_NAMES,
            applied_names=(subject.MIGRATION_NAMES[0],),
            table_names={subject.OUTSTANDING_TABLE, subject.BLACKLISTED_TABLE},
        )
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(subject.BlacklistBoundaryError):
                subject.validate_source_state(**(defaults | changes))

    def test_untracked_tables_denied(self):
        with self.assertRaises(subject.BlacklistBoundaryError):
            subject.validate_source_state(
                runtime_version="5.5.1",
                disk_names=subject.MIGRATION_NAMES,
                applied_names=(),
                table_names={subject.OUTSTANDING_TABLE, subject.BLACKLISTED_TABLE},
            )

    def test_forward_plan_only_exact_suffix(self):
        def plan(names):
            return [(SimpleNamespace(app_label="token_blacklist", name=name), False) for name in names]
        for offset in range(len(subject.MIGRATION_NAMES)):
            self.assertTrue(subject.is_reviewed_plan(
                plan(subject.MIGRATION_NAMES[offset:]), allow_blacklist=True
            ))
        for names in [
            ("0013_blacklist",),
            (subject.MIGRATION_NAMES[0], subject.MIGRATION_NAMES[-1]),
            tuple(reversed(subject.MIGRATION_NAMES)),
        ]:
            self.assertFalse(subject.is_reviewed_plan(plan(names), allow_blacklist=True))
        self.assertFalse(subject.is_reviewed_plan(plan(subject.MIGRATION_NAMES)))


if __name__ == "__main__":
    unittest.main()
