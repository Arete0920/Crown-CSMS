"""No-network regression tests for the DEV blacklist read-only inventory."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import read_dev_blacklist_state as subject

SHA = "a" * 40
URL = "postgresql://synthetic:private-password@crown-pg-dev.postgres.database.azure.com/crown?sslmode=require"


class Cursor:
    def __init__(self, migrations=(), tables=(False, False), readonly=True):
        self.migrations, self.tables, self.readonly = migrations, tables, readonly
        self.queries = []
        self.last = ""

    def __enter__(self): return self
    def __exit__(self, *args): return None

    def execute(self, sql, params=None):
        self.last = sql
        self.queries.append((sql, params))
        assert sql.startswith(("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY",
                               "SHOW transaction_read_only", "SELECT "))

    def fetchone(self):
        if self.last.startswith("SHOW"): return ("on" if self.readonly else "off",)
        if self.last.startswith("SELECT current_database"): return ("crown", "public", False)
        if self.last.startswith("SELECT ssl"): return (True,)
        if self.last.startswith("SELECT to_regclass"): return self.tables
        raise AssertionError(self.last)

    def fetchall(self):
        if self.last.startswith("SELECT name FROM"): return [(m,) for m in self.migrations]
        if self.last.startswith("SELECT table_name"): return []
        raise AssertionError(self.last)


class Connection:
    def __init__(self, cursor): self.fixture = cursor
    def __enter__(self): return self
    def __exit__(self, *args): return None
    @contextlib.contextmanager
    def transaction(self): yield
    def cursor(self): return self.fixture


class InventoryTests(unittest.TestCase):
    def test_source_checks_head_and_main_ancestry(self):
        good = Mock(side_effect=[SimpleNamespace(returncode=0, stdout=SHA),
                                 SimpleNamespace(returncode=0)])
        subject.verify_accepted_source(SHA, runner=good)
        self.assertEqual(good.call_args_list[1].args[0],
                         ["git", "merge-base", "--is-ancestor", SHA, "origin/main"])
        with self.assertRaises(subject.EvidenceBlocked):
            subject.verify_accepted_source("main", runner=Mock())

    def test_configuration_queries_only_dev_database_setting(self):
        read = Mock(side_effect=[
            {"name": "crown-api-dev", "defaultHostName": "crown-api-dev.azurewebsites.net"},
            [{"name": k, "value": v} for k, v in {
                "CROWN_ENV": "dev", "ENVIRONMENT": "dev",
                "DJANGO_ENV": "development", "DATABASE_URL": URL}.items()],
        ])
        self.assertEqual(subject.read_dev_database_setting(read=read), (URL, "crown"))
        self.assertNotIn("SECRET_KEY", subject.SETTING_FILTER)
        self.assertIn("--query", read.call_args.args)
        self.assertNotIn("create", repr(read.call_args_list))

    def test_schema_classification_is_not_authority(self):
        self.assertEqual(subject.classify_schema([], {"outstanding":False, "blacklisted":False}, {}),
                         "CLEAN_UNINITIALIZED")
        self.assertEqual(subject.classify_schema(["0013_blacklist"], {"outstanding":True, "blacklisted":True}, {}),
                         "RECONCILIATION_REQUIRED")
        self.assertEqual(subject.classify_schema(subject.VENDOR_MIGRATIONS,
                                                 {"outstanding":True,"blacklisted":True},
                                                 {"outstanding":True,"blacklisted":True}),
                         "VENDOR_HISTORY_AND_TABLES_PRESENT")

    def test_connection_is_read_only_and_metadata_only(self):
        with TemporaryDirectory() as folder:
            ca = Path(folder) / "ca.pem"
            ca.write_text("synthetic")
            cursor = Cursor()
            connect = Mock(return_value=Connection(cursor))
            result = subject.inspect_database(URL, "crown", connector=connect, ca_file=ca)
            self.assertEqual(result["schema_classification"], "CLEAN_UNINITIALIZED")
            self.assertEqual(cursor.queries[0][0],
                             "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self.assertEqual(connect.call_args.kwargs["sslmode"], "verify-full")
            self.assertIn("default_transaction_read_only=on", connect.call_args.kwargs["options"])
            cursor.readonly = False
            with self.assertRaises(subject.EvidenceBlocked):
                subject.inspect_database(URL, "crown", connector=connect, ca_file=ca)

    def test_error_output_does_not_expose_connection_string(self):
        output = io.StringIO()
        with patch.object(subject, "verify_accepted_source"), patch.object(
            subject, "read_dev_database_setting", side_effect=RuntimeError(URL)
        ), contextlib.redirect_stdout(output):
            self.assertEqual(subject.main(["--expected-sha", SHA]), 1)
        data = json.loads(output.getvalue())
        self.assertEqual(data["status"], "BLOCKED")
        self.assertFalse(data["activation_authorized"])
        self.assertNotIn("private-password", output.getvalue())


if __name__ == "__main__":
    unittest.main()
