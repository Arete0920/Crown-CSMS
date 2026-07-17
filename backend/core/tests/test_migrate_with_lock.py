from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


COMMAND_MODULE = "core.management.commands.migrate_with_lock"


class MigrateWithLockCommandTests(SimpleTestCase):
    @patch(f"{COMMAND_MODULE}.connection")
    def test_refuses_non_postgresql_without_explicit_proof_flag(self, mock_connection):
        mock_connection.vendor = "sqlite"

        with self.assertRaisesMessage(CommandError, "requires PostgreSQL advisory locking"):
            call_command("migrate_with_lock", verbosity=0)

    @patch(f"{COMMAND_MODULE}.call_command")
    @patch(f"{COMMAND_MODULE}.connection")
    def test_allows_non_postgresql_only_for_local_or_ci_proof(
        self,
        mock_connection,
        mock_call_command,
    ):
        mock_connection.vendor = "sqlite"

        call_command(
            "migrate_with_lock",
            allow_non_postgresql=True,
            verbosity=0,
        )

        mock_call_command.assert_called_once_with(
            "migrate",
            interactive=False,
            check=False,
            verbosity=0,
        )

    @patch(f"{COMMAND_MODULE}.call_command")
    @patch(f"{COMMAND_MODULE}.connection")
    def test_postgresql_lock_is_acquired_and_released(
        self,
        mock_connection,
        mock_call_command,
    ):
        mock_connection.vendor = "postgresql"
        cursor = MagicMock()
        cursor.fetchone.side_effect = [(True,), (True,)]
        mock_connection.cursor.return_value.__enter__.return_value = cursor

        call_command("migrate_with_lock", lock_timeout_seconds=0, verbosity=0)

        self.assertEqual(
            cursor.execute.call_args_list[0].args,
            ("SELECT pg_try_advisory_lock(%s)", [2026071701]),
        )
        self.assertEqual(
            cursor.execute.call_args_list[1].args,
            ("SELECT pg_advisory_unlock(%s)", [2026071701]),
        )
        mock_call_command.assert_called_once()

    @patch(f"{COMMAND_MODULE}.time.sleep")
    @patch(f"{COMMAND_MODULE}.time.monotonic", side_effect=[10, 10])
    @patch(f"{COMMAND_MODULE}.connection")
    def test_postgresql_lock_contention_fails_closed(
        self,
        mock_connection,
        _mock_monotonic,
        mock_sleep,
    ):
        mock_connection.vendor = "postgresql"
        cursor = MagicMock()
        cursor.fetchone.return_value = (False,)
        mock_connection.cursor.return_value.__enter__.return_value = cursor

        with self.assertRaisesMessage(CommandError, "Timed out waiting"):
            call_command("migrate_with_lock", lock_timeout_seconds=0, verbosity=0)

        mock_sleep.assert_not_called()
