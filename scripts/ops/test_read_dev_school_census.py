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


    def test_sanitized_readback_reports_only_literal_demo_booleans(self):
        rows = [
            {"name": "CROWN_SANDBOX_ALLOW_OPEN_SESSION", "value": "false"},
            {"name": "CROWN_HOSTED_JIREH_DEMO_ENABLED", "value": "TRUE"},
            {"name": "DATABASE_URL", "value": URL},
        ]
        read = Mock(return_value=rows)
        result = subject.read_demo_flag_markers(read=read)
        self.assertEqual(result, {
            "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "false",
            "CROWN_HOSTED_JIREH_DEMO_ENABLED": "true",
        })
        self.assertEqual(read.call_args.args[:4],
                         ("webapp", "config", "appsettings", "list"))
        self.assertEqual(read.call_args.args[-2:],
                         ("--query", subject.DEMO_FLAG_FILTER))
        self.assertNotIn("private-password", json.dumps(result))
        self.assertNotIn(URL, json.dumps(result))

    def test_sanitized_readback_missing_secret_or_duplicate_is_unverified(self):
        first, second = subject.DEMO_FLAG_NAMES
        for rows in (
            [],
            [{"name": first, "value": "@Microsoft.KeyVault(SecretUri=https://private)"}],
            [{"name": first, "value": "some private value"}],
            [{"name": first, "value": "true"}, {"name": first, "value": "false"}],
            [{"name": first, "value": "true"}, None],
            {"wrong": "shape"}, None,
        ):
            with self.subTest(rows=rows):
                evidence = subject.read_demo_flag_markers(read=lambda *args: rows)
                self.assertEqual(evidence, {first: "UNVERIFIED", second: "UNVERIFIED"})
                self.assertNotIn("private", json.dumps(evidence))

    def test_sanitized_readback_azure_failure_never_emits_secret(self):
        def forbidden(*args):
            raise RuntimeError("subscription-secret-123")
        evidence = subject.read_demo_flag_markers(read=forbidden)
        self.assertEqual(evidence, {
            key: "UNVERIFIED" for key in subject.DEMO_FLAG_NAMES
        })
        self.assertNotIn("subscription-secret-123", json.dumps(evidence))

    def test_main_records_flag_evidence_after_dev_identity_check_only(self):
        out = io.StringIO()
        with patch.object(subject, "verify_accepted_source"), patch.object(
            subject, "read_dev_database_setting", return_value=(URL, "crown"),
        ), patch.object(subject, "read_demo_flag_markers", return_value={
            "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "false",
            "CROWN_HOSTED_JIREH_DEMO_ENABLED": "UNVERIFIED",
        }) as read_flags, patch.object(
            subject, "inspect_database", return_value={"school_count": 0},
        ), contextlib.redirect_stdout(out):
            self.assertEqual(subject.main(["--expected-sha", SHA]), 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["dev_demo_appsettings"], {
            "CROWN_SANDBOX_ALLOW_OPEN_SESSION": "false",
            "CROWN_HOSTED_JIREH_DEMO_ENABLED": "UNVERIFIED",
        })
        read_flags.assert_called_once_with()

    def test_main_never_reads_flags_if_dev_target_rejected(self):
        out = io.StringIO()
        with patch.object(subject, "verify_accepted_source"), patch.object(
            subject, "read_dev_database_setting",
            side_effect=subject.EvidenceBlocked("dev_app_identity_not_verified"),
        ), patch.object(subject, "read_demo_flag_markers") as read_flags, contextlib.redirect_stdout(out):
            self.assertEqual(subject.main(["--expected-sha", SHA]), 1)
        read_flags.assert_not_called()
        self.assertEqual(json.loads(out.getvalue())["status"], "BLOCKED")



if __name__ == "__main__":
    unittest.main()
