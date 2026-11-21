import contextlib
import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from unittest.mock import Mock

p = Path(__file__).with_name('crown637_history_readonly.py')
spec = importlib.util.spec_from_file_location('subject', p)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

SCHOOL = '19801b59-8c05-4c84-9312-5d792e4e839d'
FAKE_URL = 'postgresql://no-real-credentials@dev.example.test/crown'


class Cursor:
    def __init__(self, rows=None, readonly='on', tls=True):
        self.rows = rows if rows is not None else [(SCHOOL, 2, 1, 2, 1, 0, 0, 1, 0)]
        self.readonly, self.tls, self.queries, self.last = readonly, tls, [], ''

    def __enter__(self): return self
    def __exit__(self, *a): return None
    def execute(self, sql):
        self.queries.append(sql)
        self.last = sql
        assert sql.startswith(('SET TRANSACTION', 'SHOW ', 'SELECT '))
    def fetchone(self):
        if self.last.startswith('SHOW '): return (self.readonly,)
        if self.last.startswith('SELECT current_database'): return ('crown', 'public', False)
        if self.last.startswith('SELECT ssl'): return (self.tls,)
        raise AssertionError(self.last)
    def fetchall(self):
        assert self.last == subject.READ_ONLY_SQL
        return self.rows

class Connection:
    def __init__(self, cursor): self.c = cursor
    def __enter__(self): return self
    def __exit__(self, *a): return None
    @contextlib.contextmanager
    def transaction(self): yield
    def cursor(self): return self.c


class AuditTests(unittest.TestCase):
    def collect(self, cursor, valid=True):
        with TemporaryDirectory() as td:
            cert = Path(td) / 'ca.pem'
            cert.write_text('synthetic test CA')
            connector = Mock(return_value=Connection(cursor))
            if not valid:
                validate = lambda url: 'not-the-target'
            else:
                validate = lambda url: 'crown'
            try:
                result = subject.inspect_database(FAKE_URL, 'crown', 'a' * 40,
                    validate_database_url=validate,
                    dev_host='dev.example.test', ca_file=cert, connector=connector)
                return result, connector
            except Exception:
                self.assertFalse(connector.called) if not valid else None
                raise

    def test_fixed_query_only_and_aggregate_privacy(self):
        cursor = Cursor()
        result, connector = self.collect(cursor)
        self.assertEqual(result['school_count'], 1)
        self.assertEqual(result['aggregate_candidate_counts']['legacy_app_number_candidates'], 2)
        self.assertEqual(result['aggregate_candidate_counts']['legacy_app_number_near_creation_dob_candidates'], 1)
        self.assertEqual(result['schools_with_candidates']['legacy_app_number_without_verified_identity'], 1)
        self.assertEqual(result['aggregate_candidate_counts']['canonical_marked_legacy_without_verified_identity'], 1)
        self.assertNotIn(SCHOOL, json.dumps(result))
        self.assertIn('SCREEN_ONLY', result['interpretation'])
        self.assertEqual(cursor.queries[-1], subject.READ_ONLY_SQL)
        self.assertTrue(all(x.startswith(('SET TRANSACTION', 'SHOW ', 'SELECT ')) for x in cursor.queries))
        self.assertEqual(connector.call_args.kwargs['sslmode'], 'verify-full')
        self.assertIn('default_transaction_read_only=on', connector.call_args.kwargs['options'])

    def test_identity_and_tls_gates_block_before_query(self):
        for cursor in [Cursor(readonly='off'), Cursor(tls=False)]:
            with self.assertRaises(subject.AuditBlocked):
                self.collect(cursor)
            self.assertNotIn(subject.READ_ONLY_SQL, cursor.queries)

    def test_wrong_dev_target_blocks_before_connector(self):
        with self.assertRaises(subject.AuditBlocked):
            self.collect(Cursor(), valid=False)

    def test_bad_rows_and_duplicates_block(self):
        with self.assertRaises(subject.AuditBlocked):
            subject.format_counts([])
        for rows in [[(SCHOOL, 1, 0)], [(SCHOOL, 0, 0, 0, 0, 0, 0, 0, True)],
                     [(SCHOOL, 0, 0, 0, 0, 0, 0, 0, 0)]*2, [(SCHOOL, -1, 0, 0, 0, 0, 0, 0, 0)]]:
            with self.subTest(rows=rows):
                with self.assertRaises(subject.AuditBlocked):
                    subject.format_counts(rows)

    def test_enrolled_without_canonical_student_is_included(self):
        """Historical ENROLLED rows with a missing canonical ID are candidates."""
        sql = subject.READ_ONLY_SQL
        section = sql.split("WHERE a.school_id=s.id AND a.status='ENROLLED'", 1)[1]
        section = section.split("  (SELECT COALESCE", 1)[0]
        self.assertIn("AND (a.student_id IS NULL OR NOT EXISTS (", section)
        self.assertIn("AND e.academic_year_id=a.academic_year_id)))", section)

    def test_only_readonly_sql_contract(self):
        sql = subject.READ_ONLY_SQL.upper()
        # PostgreSQL SUM(bigint) returns numeric/Decimal; the aggregate packet
        # must return bigint/int for format_counts to accept a valid result.
        self.assertIn("COALESCE(SUM(D.N-1), 0)::BIGINT", sql)
        self.assertIn("A.NOTES_INTERNAL LIKE '%CANONICAL_APPLICATION_ID=%'", sql)
        for forbidden in ['INSERT INTO ', 'UPDATE PUBLIC.', 'DELETE FROM ', 'ALTER TABLE ',
                          'DROP TABLE ', 'COPY ', 'CREATE TABLE ', 'DO $$', 'EXECUTE ']:
            self.assertNotIn(forbidden, sql)
        for table in ['CORE_STUDENT', 'CORE_STUDENTIDENTITYLINK',
                      'ADMISSIONS_ADMISSIONSAPPLICATION', 'CORE_ENROLLMENT', 'CORE_SCHOOL',
                      'PUBLIC.APPLICANT', 'PUBLIC.APPLICATION']:
            self.assertIn(table, sql)

class DispatchSelectionTests(unittest.TestCase):
    def context(self, inputs=None, **overrides):
        with TemporaryDirectory() as td:
            e = Path(td) / "event.json"
            e.write_text(json.dumps({"inputs": inputs or {}}), encoding="utf-8")
            env = {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_EVENT_PATH": str(e),
                "GITHUB_REPOSITORY": "Arete0920/Crown-CSMS",
                "GITHUB_REF": "refs/heads/main",
                "GITHUB_SHA": "a"*40,
            }
            env.update(overrides)
            return subject.requested_from_event(env)

    def test_push_and_ordinary_dispatch_do_not_run_audit(self):
        self.assertFalse(self.context({}))
        self.assertFalse(self.context({"confirm_dev_support": "crown269-reference-metadata-only"}))
        self.assertFalse(self.context({"confirm_dev_support": subject.MANUAL_MARKER}, GITHUB_EVENT_NAME="push"))

    def test_exact_manual_sha_and_default_off_flags(self):
        self.assertTrue(self.context({"confirm_dev_support": subject.MANUAL_MARKER,
                                      "expected_sha": "a"*40,
                                      "apply_reviewed_support": "false"}))

    def test_mismatched_sha_ref_repo_and_mixed_modes_are_denied(self):
        base = {"confirm_dev_support": subject.MANUAL_MARKER, "expected_sha": "a"*40}
        for extra, env in [({"apply_reviewed_blacklist": "true"}, {}),
                           ({"inspect_migration_plan": "true"}, {}),
                           ({"confirm_dev_legacy_refresh": "migrate-dev-legacy-refresh"}, {}),
                           ({"dev_recovery_receipt": "https://example.com"}, {}),
                           ({}, {"GITHUB_SHA": "b"*40}),
                           ({}, {"GITHUB_REF": "refs/heads/feature"}),
                           ({}, {"GITHUB_REPOSITORY": "other/repo"})]:
            with self.subTest(extra=extra, env=env):
                with self.assertRaises(subject.AuditBlocked):
                    self.context(dict(base, **extra), **env)

    def test_malformed_event_fails_closed(self):
        with TemporaryDirectory() as td:
            p = Path(td) / 'event.json'
            p.write_text('not json')
            with self.assertRaises(subject.AuditBlocked):
                subject.requested_from_event({"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_EVENT_PATH": str(p)})

if __name__ == '__main__':
    unittest.main()
