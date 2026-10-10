import importlib.util
from pathlib import Path
import unittest

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


if __name__ == '__main__':
    unittest.main()
