import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_negative_skipped_job_timing_is_recorded_not_counted(self):
        run = {
            'id': 13, 'name': 'Workflow', 'head_sha': 'b' * 40,
            'html_url': 'https://example.invalid/13',
            'created_at': '2026-10-26T11:00:00Z',
            'run_started_at': '2026-10-26T11:01:00Z',
        }
        jobs = [
            {'name': 'skipped-stage', 'conclusion': 'skipped',
             'started_at': '2026-10-26T11:06:00Z',
             'completed_at': '2026-10-26T11:05:50Z'},
            {'name': 'real-stage', 'conclusion': 'success',
             'started_at': '2026-10-26T11:02:00Z',
             'completed_at': '2026-10-26T11:04:00Z'},
        ]
        result = metrics.summarize(run, jobs, [])
        self.assertFalse(result['runner_time_complete'])
        self.assertEqual(result['invalid_job_timing'], ['skipped-stage'])
        self.assertFalse(result['invalid_queue_timing'])
        self.assertEqual(result['runner_seconds'], 120)
        self.assertEqual(result['queue_seconds'], 60)

    def test_negative_queue_timing_is_recorded_as_unknown(self):
        run = {
            'id': 14, 'name': 'Workflow', 'head_sha': 'b' * 40,
            'html_url': 'https://example.invalid/14',
            'created_at': '2026-10-26T11:04:00Z',
            'run_started_at': '2026-10-26T11:03:00Z',
        }
        result = metrics.summarize(run, [
            {'name': 'real-stage', 'conclusion': 'success',
             'started_at': '2026-10-26T11:05:00Z',
             'completed_at': '2026-10-26T11:06:00Z'},
        ], [])
        self.assertTrue(result['invalid_queue_timing'])
        self.assertIsNone(result['queue_seconds'])
        self.assertEqual(result['invalid_job_timing'], [])
        self.assertTrue(result['runner_time_complete'])
        self.assertEqual(result['runner_seconds'], 60)

    def test_malformed_timestamps_still_fail(self):
        with self.assertRaises(ValueError):
            metrics.seconds('not-a-time', '2026-10-26T11:00:00Z')

    def test_queue_only_anomaly_does_not_claim_runner_time_is_incomplete(self):
        run = {
            'id': 14, 'name': 'Workflow', 'head_sha': 'b' * 40,
            'html_url': 'https://example.invalid/14', 'conclusion': 'success',
            'created_at': '2026-10-26T11:04:00Z',
            'run_started_at': '2026-10-26T11:03:00Z',
        }
        responses = iter([
            {'workflow_runs': [run]},
            {'total_count': 1, 'jobs': [
                {'name': 'real-stage', 'conclusion': 'success',
                 'started_at': '2026-10-26T11:05:00Z',
                 'completed_at': '2026-10-26T11:06:00Z'},
            ]},
            {'total_count': 1, 'artifacts': [{'size_in_bytes': 123}]},
        ])

        def fetch_response(request, timeout):
            return io.BytesIO(json.dumps(next(responses)).encode())

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / 'ci-metrics.json'
            summary_path = Path(directory) / 'summary.md'
            with patch.dict(os.environ, {
                'GH_TOKEN': 'unit-test-placeholder',
                'GITHUB_STEP_SUMMARY': str(summary_path),
            }), patch.object(metrics, 'urlopen', side_effect=fetch_response), \
                    patch.object(metrics, 'Path', return_value=report_path):
                metrics.main()
            report = json.loads(report_path.read_text())
            self.assertEqual(report['timing_anomaly_count'], 1)
            self.assertEqual(report['artifact_bytes'], 123)
            self.assertTrue(report['runs'][0]['runner_time_complete'])
            self.assertIsNone(report['runs'][0]['queue_seconds'])
            summary = summary_path.read_text()
            self.assertIn('timing accounting incomplete', summary)
            self.assertNotIn('runner accounting incomplete', summary)

    def test_invalid_negative_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            metrics.seconds('2026-10-09T12:03:00Z', '2026-10-09T12:01:00Z')


if __name__ == '__main__':
    unittest.main()
