import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import json
import os
import tempfile

spec = importlib.util.spec_from_file_location('ci_metrics', Path(__file__).with_name('report_ci_metrics.py'))
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class MetricsTests(unittest.TestCase):
    def test_incomplete_job_time_is_not_reported_as_complete(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40, 'html_url': 'https://example.invalid'}
        result = metrics.summarize(run, [{'name': 'tests'}], [])
        self.assertFalse(result['runner_time_complete'])
        self.assertIsNone(result['queue_seconds'])

    def test_failure_artifact_and_retry_evidence_are_preserved(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40, 'html_url': 'https://example.invalid',
               'run_attempt': 2, 'conclusion': 'failure', 'created_at': '2026-10-09T12:00:00Z',
               'run_started_at': '2026-10-09T12:01:00Z'}
        result = metrics.summarize(run, [{'name': 'tests', 'conclusion': 'failure',
                 'started_at': '2026-10-09T12:01:00Z', 'completed_at': '2026-10-09T12:03:00Z'}],
                 [{'size_in_bytes': 123}])
        self.assertEqual(result['queue_seconds'], 60)
        self.assertEqual(result['runner_seconds'], 120)
        self.assertEqual(result['artifact_bytes'], 123)
        self.assertEqual(result['failed_jobs'], ['tests'])
        self.assertEqual(result['attempt'], 2)

    def test_invalid_negative_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            metrics.seconds('2026-10-09T12:03:00Z', '2026-10-09T12:01:00Z')

    def test_invalid_job_timing_retains_failure_without_inventing_duration(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40, 'html_url': 'https://example.invalid'}
        jobs = [{'id': 7, 'name': 'invalid', 'conclusion': 'failure',
                 'started_at': '2026-10-09T12:03:00Z', 'completed_at': '2026-10-09T12:01:00Z'},
                {'id': 8, 'name': 'valid', 'started_at': '2026-10-09T12:01:00Z',
                 'completed_at': '2026-10-09T12:03:00Z'}]
        result = metrics.summarize(run, jobs, [{'size_in_bytes': 123}])
        self.assertEqual(result['timing_errors'], ['job:7'])
        self.assertFalse(result['runner_time_complete'])
        self.assertEqual(result['runner_seconds'], 120)
        self.assertEqual(result['failed_jobs'], ['invalid'])
        self.assertEqual(result['artifact_bytes'], 123)

    def test_invalid_queue_is_unknown_while_valid_runner_time_is_preserved(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40, 'html_url': 'https://example.invalid',
               'created_at': '2026-10-09T12:03:00Z', 'run_started_at': '2026-10-09T12:01:00Z'}
        result = metrics.summarize(run, [{'name': 'valid', 'started_at': '2026-10-09T12:01:00Z',
                                         'completed_at': '2026-10-09T12:03:00Z'}], [])
        self.assertIsNone(result['queue_seconds'])
        self.assertEqual(result['timing_errors'], ['queue'])
        self.assertTrue(result['runner_time_complete'])
        self.assertEqual(result['runner_seconds'], 120)

    def test_invalid_sample_writes_evidence_then_exits_unsuccessfully(self):
        from io import BytesIO
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40, 'html_url': 'https://example.invalid',
               'conclusion': 'failure'}
        responses = [
            {'workflow_runs': [run]},
            {'total_count': 1, 'jobs': [{'id': 7, 'name': 'invalid', 'conclusion': 'failure',
                'started_at': '2026-10-09T12:03:00Z', 'completed_at': '2026-10-09T12:01:00Z'}]},
            {'total_count': 1, 'artifacts': [{'size_in_bytes': 123}]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / 'ci-metrics.json'
            summary_path = Path(directory) / 'summary.md'
            with patch.dict(os.environ, {'GH_TOKEN': 'synthetic-test-only',
                                        'GITHUB_STEP_SUMMARY': str(summary_path)}), \
                 patch.object(metrics, 'urlopen', side_effect=[BytesIO(json.dumps(r).encode())
                                                             for r in responses]), \
                 patch.object(metrics, 'Path', return_value=report_path):
                with self.assertRaises(SystemExit) as failure:
                    metrics.main()
            self.assertNotEqual(failure.exception.code, 0)
            report = json.loads(report_path.read_text())
            self.assertEqual(report['invalid_timing_runs'], [1])
            self.assertFalse(report['runner_time_complete'])
            self.assertEqual(report['runner_minutes'], 0)
            self.assertEqual(report['artifact_bytes'], 123)
            self.assertEqual(report['conclusions'], {'failure': 1})
            self.assertIn('Timing is incomplete or invalid', summary_path.read_text())

    def test_step_free_skipped_jobs_have_lifecycle_receipts_not_runner_time(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40,
               'html_url': 'https://example.invalid'}
        for started, completed, lifecycle_status in (
            ('2026-10-26T20:13:14Z', '2026-10-26T20:13:13Z', 'invalid'),
            ('2026-10-26T20:13:13Z', '2026-10-26T20:13:14Z', 'valid'),
            (None, None, 'missing'),
        ):
            with self.subTest(lifecycle_status=lifecycle_status):
                skipped = {'id': 7, 'name': 'conditional', 'status': 'completed',
                           'conclusion': 'skipped', 'steps': [],
                           'started_at': started, 'completed_at': completed}
                executed = {'id': 8, 'name': 'executed', 'conclusion': 'success',
                            'started_at': '2026-10-26T20:11:00Z',
                            'completed_at': '2026-10-26T20:13:00Z'}
                result = metrics.summarize(run, [skipped, executed], [])
                self.assertEqual(result['runner_seconds'], 120)
                self.assertTrue(result['runner_time_complete'])
                self.assertEqual(result['timing_errors'], [])
                self.assertEqual(result['skipped_jobs'], [{
                    'job_id': 7, 'name': 'conditional', 'started_at': started,
                    'completed_at': completed, 'lifecycle_timing_status': lifecycle_status,
                }])

    def test_skipped_classification_requires_complete_nonexecution_evidence(self):
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40,
               'html_url': 'https://example.invalid'}
        base = {'id': 7, 'name': 'conditional', 'status': 'completed',
                'conclusion': 'skipped', 'steps': [],
                'started_at': '2026-10-26T20:13:14Z',
                'completed_at': '2026-10-26T20:13:13Z'}
        for changes in ({'status': 'in_progress'}, {'conclusion': 'failure'},
                        {'steps': [{'name': 'executed step'}]}, {'steps': None}):
            with self.subTest(changes=changes):
                result = metrics.summarize(run, [dict(base, **changes)], [])
                self.assertFalse(result['runner_time_complete'])
                self.assertEqual(result['timing_errors'], ['job:7'])
                self.assertEqual(result['skipped_jobs'], [])

    def test_skipped_lifecycle_anomaly_is_reported_without_failing_runner_accounting(self):
        from io import BytesIO
        run = {'id': 1, 'name': 'Tests', 'head_sha': 'a' * 40,
               'html_url': 'https://example.invalid', 'conclusion': 'success'}
        responses = [
            {'workflow_runs': [run]},
            {'total_count': 1, 'jobs': [
                {'id': 7, 'name': 'conditional', 'status': 'completed',
                 'conclusion': 'skipped', 'steps': [],
                 'started_at': '2026-10-26T20:13:14Z',
                 'completed_at': '2026-10-26T20:13:13Z'},
                {'id': 8, 'name': 'executed', 'conclusion': 'success',
                 'started_at': '2026-10-26T20:11:00Z',
                 'completed_at': '2026-10-26T20:13:00Z'},
            ]},
            {'total_count': 1, 'artifacts': [{'size_in_bytes': 123}]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / 'ci-metrics.json'
            summary_path = Path(directory) / 'summary.md'
            with patch.dict(os.environ, {'GH_TOKEN': 'synthetic-test-only',
                                        'GITHUB_STEP_SUMMARY': str(summary_path)}), \
                 patch.object(metrics, 'urlopen', side_effect=[BytesIO(json.dumps(r).encode())
                                                             for r in responses]), \
                 patch.object(metrics, 'Path', return_value=report_path):
                metrics.main()
            report = json.loads(report_path.read_text())
            self.assertEqual(report['invalid_timing_runs'], [])
            self.assertTrue(report['runner_time_complete'])
            self.assertEqual(report['runner_minutes'], 2)
            self.assertEqual(report['skipped_job_count'], 1)
            self.assertEqual(report['skipped_lifecycle_anomaly_count'], 1)
            self.assertEqual(report['artifact_bytes'], 123)
            self.assertIn('1 skipped-job lifecycle timing anomalies', summary_path.read_text())


if __name__ == '__main__':
    unittest.main()
