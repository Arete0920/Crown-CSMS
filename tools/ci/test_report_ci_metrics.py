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


if __name__ == '__main__':
    unittest.main()

