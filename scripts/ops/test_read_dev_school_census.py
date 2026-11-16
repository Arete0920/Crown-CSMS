"""Offline contract tests for DEV read-only school census and evidence privacy."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import read_dev_school_census as subject

SHA = "a" * 40
URL = "postgresql://synthetic:private-password@crown-pg-dev.postgres.database.azure.com/crown?sslmode=require"
HERITAGE = (subject.HERITAGE_ID, subject.HERITAGE_NAME, None, 286, 700, 0, 0)
BUYER = ("11111111-2222-4333-8444-555555555555", subject.BUYER_NAME, SHA, 1, 1, 2, 1)


class Cursor:
    def __init__(self, *, rows=(HERITAGE, BUYER), readonly=True, tls=True):
        self.rows, self.readonly, self.tls = rows, readonly, tls
        self.queries = []
        self.last = ""

    def __enter__(self): return self
    def __exit__(self, *args): return None

    def execute(self, sql):
        self.last = sql
        self.queries.append(sql)
        assert sql.startswith((
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY",
            "SHOW transaction_read_only", "SELECT ",
        ))

    def fetchone(self):
        if self.last.startswith("SHOW"): return ("on" if self.readonly else "off",)
        if self.last.startswith("SELECT current_database"): return ("crown", "public", False)
        if self.last.startswith("SELECT ssl"): return (self.tls,)
        raise AssertionError(self.last)

    def fetchall(self):
        assert self.last == subject.CENSUS_SQL
        return self.rows


class Connection:
    def __init__(self, cursor): self.fixture = cursor
    def __enter__(self): return self
    def __exit__(self, *args): return None

    @contextlib.contextmanager
    def transaction(self): yield

    def cursor(self): return self.fixture


class CensusTests(unittest.TestCase):
    def test_strict_readonly_tls_and_distinct_school_counts(self):
        with TemporaryDirectory() as folder:
            ca = Path(folder) / "ca.pem"
            ca.write_text("synthetic")
            cursor = Cursor()
            connector = Mock(return_value=Connection(cursor))
            result = subject.inspect_database(URL, "crown", SHA, connector=connector, ca_file=ca)
            self.assertEqual(result["school_count"], 2)
            self.assertEqual(result["buyer_workspace_count"], 1)
            self.assertEqual(result["totals"]["core_families"], 287)
            self.assertEqual(result["totals"]["portal_households"], 2)
            self.assertEqual([row["classification"] for row in result["schools"]],
                             ["canonical_heritage", "invite_owned_buyer"])
            self.assertTrue(result["schools"][1]["buyer_workspace_exact_source"])
            self.assertNotIn(subject.HERITAGE_ID, json.dumps(result))
            self.assertNotIn(subject.BUYER_NAME, json.dumps(result))
            self.assertIn("default_transaction_read_only=on", connector.call_args.kwargs["options"])
            self.assertEqual(connector.call_args.kwargs["sslmode"], "verify-full")
            self.assertEqual(cursor.queries[0], "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self.assertTrue(all(query.startswith(("SELECT ", "SHOW ", "SET TRANSACTION "))
                                for query in cursor.queries))

    def test_readonly_and_tls_failure_stop_before_census(self):
        with TemporaryDirectory() as folder:
            ca = Path(folder) / "ca.pem"
            ca.write_text("synthetic")
            for cursor in (Cursor(readonly=False), Cursor(tls=False)):
                with self.subTest(cursor=cursor):
                    with self.assertRaises(subject.CensusBlocked):
                        subject.inspect_database(
                            URL, "crown", SHA,
                            connector=Mock(return_value=Connection(cursor)), ca_file=ca)
                    self.assertNotIn(subject.CENSUS_SQL, cursor.queries)

    def test_named_buyer_without_workspace_is_not_an_invited_buyer(self):
        row = ("11111111-2222-4333-8444-555555555555", subject.BUYER_NAME, None, 0, 0, 0, 0)
        self.assertEqual(subject.format_rows([row], SHA)["schools"][0]["classification"],
                         "buyer_name_without_workspace")

    def test_bad_rows_rejected(self):
        for row in (
            ("invalid-id", subject.HERITAGE_NAME, None, 286, 700, 0, 0),
            (subject.HERITAGE_ID, subject.HERITAGE_NAME, None, -1, 700, 0, 0),
            (subject.HERITAGE_ID, subject.HERITAGE_NAME, "bad-source", 1, 0, 0, 0),
        ):
            with self.subTest(row=row):
                with self.assertRaises(subject.CensusBlocked):
                    subject.format_rows([row], SHA)
        with self.assertRaises(subject.CensusBlocked):
            subject.format_rows([HERITAGE] * (subject.MAX_SCHOOLS + 1), SHA)

    def test_error_packet_never_leaks_database_url(self):
        out = io.StringIO()
        with patch.object(subject, "verify_accepted_source"), patch.object(
            subject, "read_dev_database_setting", side_effect=RuntimeError(URL),
        ), patch.object(subject, "inspect_database") as inspect, contextlib.redirect_stdout(out):
            self.assertEqual(subject.main(["--expected-sha", SHA]), 1)
        packet = json.loads(out.getvalue())
        self.assertEqual(packet["status"], "BLOCKED")
        self.assertEqual(packet["reason"], "census_evidence_unavailable")
        self.assertFalse(packet["database_writes_authorized"])
        self.assertNotIn("private-password", out.getvalue())
        inspect.assert_not_called()

    def test_rejects_invalid_source_before_azure(self):
        out = io.StringIO()
        with patch.object(
            subject, "verify_accepted_source",
            side_effect=subject.EvidenceBlocked("accepted_source_sha_required"),
        ) as check, patch.object(
            subject, "read_dev_database_setting"
        ) as azure, contextlib.redirect_stdout(out):
            self.assertEqual(subject.main(["--expected-sha", "main"]), 1)
        check.assert_called_once_with("main")
        azure.assert_not_called()
        self.assertEqual(json.loads(out.getvalue())["stage"], "source")


if __name__ == "__main__":
    unittest.main()
