"""Synthetic/no-network tests of the legacy 0014 migration boundary."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import reviewed_legacy_refresh_migrations as subject


def node(app="crown_api", name="0014_legacy_refresh_consumption"):
    return SimpleNamespace(app_label=app, name=name)


class FakeConnection:
    def __init__(self, *, tables=True, columns=None, constraints=None):
        self.constraints = constraints if constraints is not None else {
            "unique": {"unique": True, "columns": ["token_digest"]},
            "fk": {"foreign_key": (subject.CROWN_USER_TABLE, "id"), "columns": ["user_id"]},
            "expiry": {"index": True, "columns": ["expires_at"]},
        }
        self.columns = subject.COLUMNS if columns is None else columns
        self.introspection = SimpleNamespace(
            table_names=lambda: [subject.TABLE] if tables else [],
            get_table_description=lambda c, t: [SimpleNamespace(name=n) for n in self.columns],
            get_constraints=lambda c, t: self.constraints,
        )
    def cursor(self):
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *args): return False
        return Cursor()


class LegacyBoundaryTests(unittest.TestCase):
    def test_reviewed_source_digest_and_modified_bytes_fail_closed(self):
        root = Path(__file__).resolve().parents[2]
        subject.verify_source(root)
        for changed in (subject.INQUIRY, subject.REVIEWED):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temp:
                for app, name in (subject.INQUIRY, subject.REVIEWED):
                    relative = Path("backend") / app / "migrations" / (name + ".py")
                    fake = Path(temp) / relative
                    fake.parent.mkdir(parents=True, exist_ok=True)
                    fake.write_bytes((root / relative).read_bytes())
                fake = Path(temp) / "backend" / changed[0] / "migrations" / (changed[1] + ".py")
                fake.write_bytes(b"unexpected")
                with self.assertRaisesRegex(subject.LegacyBoundaryError, "digest_mismatch"):
                    subject.verify_source(Path(temp))

    def test_empty_and_legacy_only_plans_remain_reviewed(self):
        self.assertEqual(subject.validate_plan([]), [])
        self.assertEqual(subject.validate_plan([(node(), False)]), [subject.REVIEWED])
        for plan in ([(node(), True)], [(node("other"), False)],
                     [(node(), False), (node("other"), False)],
                     [(node("other"), False), (node(), False)]):
            with self.subTest(plan=plan), self.assertRaises(subject.LegacyBoundaryError):
                subject.validate_plan(plan)

    def test_observed_inquiry_then_legacy_plan_is_reviewed(self):
        inquiry = node("crm_marketing", "0002_inquiry_capture")
        self.assertEqual(
            subject.validate_plan([(inquiry, False), (node(), False)]),
            [("crm_marketing", "0002_inquiry_capture"), subject.REVIEWED],
        )

    def test_combined_plan_rejects_reordering_duplicates_and_other_work(self):
        inquiry = node("crm_marketing", "0002_inquiry_capture")
        for plan in (
            [(inquiry, False)],
            [(node(), False), (inquiry, False)],
            [(inquiry, True), (node(), False)],
            [(inquiry, False), (node(), True)],
            [(inquiry, False), (inquiry, False), (node(), False)],
            [(inquiry, False), (node(), False), (node("other"), False)],
        ):
            with self.subTest(plan=plan), self.assertRaises(subject.LegacyBoundaryError):
                subject.validate_plan(plan)

    def test_preflight_rejects_untracked_or_missing_recorded_table(self):
        for applied, tables, failure in (
            (False, True, "untracked_legacy_refresh_table"),
            (True, False, "recorded_legacy_refresh_table_missing"),
        ):
            loader = SimpleNamespace(
                disk_migrations={subject.REVIEWED: object()},
                applied_migrations={subject.REVIEWED} if applied else set(),
            )
            with self.subTest(failure=failure), self.assertRaisesRegex(subject.LegacyBoundaryError, failure):
                subject.preflight(FakeConnection(tables=tables), loader)

    def test_schema_checks_unique_fk_index_and_required_columns(self):
        import sys
        recorder = SimpleNamespace(MigrationRecorder=lambda c: SimpleNamespace(
            applied_migrations=lambda: {subject.REVIEWED}))
        with patch.dict(sys.modules, {
            "django": SimpleNamespace(), "django.db": SimpleNamespace(),
            "django.db.migrations": SimpleNamespace(),
            "django.db.migrations.recorder": recorder,
        }):
            subject.verify_applied_schema(FakeConnection())
            defaults = FakeConnection().constraints
            cases = [
                (FakeConnection(columns={"id"}), "columns_missing"),
                (FakeConnection(constraints={k:v for k,v in defaults.items() if k!="unique"}), "digest_unique_missing"),
                (FakeConnection(constraints={k:v for k,v in defaults.items() if k!="fk"}), "user_foreign_key_missing"),
                (FakeConnection(constraints={k:v for k,v in defaults.items() if k!="expiry"}), "expiry_index_missing"),
            ]
            for connection, code in cases:
                with self.subTest(code=code), self.assertRaisesRegex(subject.LegacyBoundaryError, code):
                    subject.verify_applied_schema(connection)


if __name__ == "__main__":
    unittest.main()
