"""No-database tests for the reviewed SimpleJWT migration allowlist."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import reviewed_blacklist_migrations as subject


class BlacklistMigrationBoundaryTests(unittest.TestCase):
    def test_runtime_manifest_pins_reviewed_simplejwt(self):
        """The Docker/backend resolver must not silently upgrade vendor schema."""
        from pathlib import Path

        manifest = Path(__file__).resolve().parents[2] / "backend" / "requirements.txt"
        declarations = [
            line.strip() for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("djangorestframework-simplejwt")
        ]
        self.assertEqual(
            declarations, [f"djangorestframework-simplejwt=={subject.REVIEWED_VERSION}"]
        )

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

    def test_reject_other_apps_and_backward_operations_in_migration_plan(self):
        def item(app, name, backwards=False):
            return (SimpleNamespace(app_label=app, name=name), backwards)
        first = item(subject.APP_LABEL, subject.MIGRATION_NAMES[0])
        foreign = item("crm_marketing", "0002_inquiry_capture")
        self.assertFalse(subject.is_reviewed_plan([foreign], allow_blacklist=True))
        self.assertFalse(subject.is_reviewed_plan([foreign, first], allow_blacklist=True))
        self.assertFalse(subject.is_reviewed_plan([first, foreign], allow_blacklist=True))
        self.assertFalse(subject.is_reviewed_plan([item(subject.APP_LABEL, subject.MIGRATION_NAMES[0], True)], allow_blacklist=True))
        self.assertFalse(subject.is_reviewed_plan([foreign], allow_blacklist=False))
        self.assertTrue(subject.is_reviewed_plan([], allow_blacklist=False))

    def test_completed_preflight_verifies_schema_constraints(self):
        conn = SimpleNamespace(introspection=SimpleNamespace(
            table_names=lambda: [subject.OUTSTANDING_TABLE, subject.BLACKLISTED_TABLE]
        ))
        loader = SimpleNamespace(
            disk_migrations={(subject.APP_LABEL, name): object()
                             for name in subject.MIGRATION_NAMES},
            applied_migrations={(subject.APP_LABEL, name)
                                for name in subject.MIGRATION_NAMES},
        )
        with patch.object(subject, "version", return_value="5.5.1"), patch.object(
            subject, "verify_applied_schema"
        ) as verify:
            self.assertTrue(subject.preflight(conn, loader, installed=True))
            verify.assert_called_once_with(conn)
        with patch.object(subject, "version", return_value="5.5.1"), patch.object(
            subject, "verify_applied_schema",
            side_effect=subject.BlacklistBoundaryError("blacklist_unique_constraint_missing")
        ):
            with self.assertRaisesRegex(subject.BlacklistBoundaryError, "unique_constraint"):
                subject.preflight(conn, loader, installed=True)

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
