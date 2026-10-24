"""Offline invariants for DEV-only support schema staging. No Azure/database reads."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import reviewed_dev_support_migrations as stage


def node(identity, backward=False):
    return (SimpleNamespace(app_label=identity[0], name=identity[1]), backward)


class SupportStageTests(unittest.TestCase):
    def test_exact_reviewed_migration_bytes(self):
        stage.verify_source(Path(__file__).resolve().parents[2])

    def test_strict_pending_plan(self):
        for plan in (
            [], [stage.INQUIRY], [stage.LEGACY],
            [stage.INQUIRY, stage.LEGACY],
            [stage.SUPPORT_2, stage.SUPPORT_3],
            [stage.INQUIRY, stage.LEGACY, stage.SUPPORT_2, stage.SUPPORT_3],
            [stage.INQUIRY, stage.LEGACY, stage.SUPPORT_3],
        ):
            with self.subTest(plan=plan):
                self.assertEqual(stage.validate_plan([node(k) for k in plan]), plan)
        for plan in (
            [stage.SUPPORT_2], [stage.SUPPORT_3, stage.SUPPORT_2],
            [stage.SUPPORT_2, stage.LEGACY, stage.SUPPORT_3],
            [stage.INQUIRY, stage.SUPPORT_2, stage.SUPPORT_3, stage.LEGACY],
            [stage.SUPPORT_2, stage.SUPPORT_2, stage.SUPPORT_3],
            [("auth", "0001_initial")],
        ):
            with self.subTest(plan=plan), self.assertRaises(stage.SupportBoundaryError):
                stage.validate_plan([node(k) for k in plan])
        with self.assertRaises(stage.SupportBoundaryError):
            stage.validate_plan([node(stage.SUPPORT_2, True), node(stage.SUPPORT_3)])

    def test_support_stage_atomic_with_post_verification(self):
        events = []
        from contextlib import contextmanager

        @contextmanager
        def lock():
            events.append("lock")
            yield
            events.append("unlock")

        @contextmanager
        def atomic():
            events.append("transaction")
            try:
                yield
            finally:
                events.append("transaction-ended")

        states = iter([
            [node(stage.INQUIRY), node(stage.LEGACY), node(stage.SUPPORT_2), node(stage.SUPPORT_3)],
            [node(stage.INQUIRY), node(stage.LEGACY)],
        ])
        result = stage.apply_support_stage(
            acquire_lock=lock,
            verify_identity=lambda: events.append("identity"),
            read_plan=lambda: next(states),
            migrate_support=lambda: events.append("migrate-to-0003"),
            verify_ddl=lambda: events.append("ddl"),
            verify_after=lambda: events.append("verified"),
            atomic=atomic,
        )
        self.assertEqual(result, ["support.0002_ticket_attribution",
                                  "support.0003_preserve_legacy_ticket_inserts"])
        self.assertEqual(events, [
            "lock", "identity", "ddl", "transaction", "migrate-to-0003",
            "verified", "transaction-ended", "unlock",
        ])

    def test_unsafe_plan_never_migrates(self):
        mutate = Mock()
        with self.assertRaises(stage.SupportBoundaryError):
            stage.apply_support_stage(
                acquire_lock=lambda: _nothing(),
                verify_identity=lambda: None,
                read_plan=lambda: [node(stage.SUPPORT_2)],
                migrate_support=mutate,
                verify_ddl=mutate,
                verify_after=mutate,
                atomic=lambda: _nothing(),
            )
        mutate.assert_not_called()


from contextlib import contextmanager


@contextmanager
def _nothing():
    yield


if __name__ == "__main__":
    unittest.main()
