"""Guard against accidental certification, mutation and credential disclosure."""
import subprocess
import unittest
from unittest.mock import patch

from azure_classroom_preflight import EvidenceError, azure_json, collect, main


class PreflightTests(unittest.TestCase):
    def inventory(self, state='Running'):
        return [
            {'id': 'subscription', 'state': 'Enabled'}, [],
            {'id': 'app', 'plan': 'plan', 'state': state},
            {'alwaysOn': True}, {'id': 'plan'},
        ]

    def test_running_app_never_certifies_release(self):
        responses = iter(self.inventory())
        calls = []
        def read(args):
            calls.append(args)
            return next(responses)
        result = collect('subscription', 'group', 'app', 'a' * 40, read)
        self.assertEqual(result['release_status'], 'NOT VERIFIED')
        self.assertTrue(result['remaining_proofs'])
        self.assertEqual([call[:2] for call in calls], [
            ['account', 'show'], ['resource', 'list'], ['webapp', 'show'],
            ['webapp', 'config'], ['appservice', 'plan'],
        ])
        self.assertTrue(all('--query' in call for call in calls))

    def test_stopped_app_is_observed_without_mutation(self):
        responses = iter(self.inventory('Stopped'))
        result = collect('subscription', 'group', 'app', 'a' * 40, lambda _: next(responses))
        self.assertEqual(result['api']['state'], 'Stopped')
        self.assertEqual(result['release_status'], 'NOT VERIFIED')

    def test_bad_sha_refuses_reads(self):
        with self.assertRaises(EvidenceError):
            collect('subscription', 'group', 'app', 'main', lambda _: self.fail('read attempted'))

    def test_subscription_mismatch_stops_inventory(self):
        with self.assertRaises(EvidenceError):
            collect('subscription', 'group', 'app', 'a' * 40,
                    lambda _: {'id': 'other', 'state': 'Enabled'})

    def test_cli_failure_does_not_echo_stderr_secrets(self):
        with patch('azure_classroom_preflight.subprocess.run', return_value=
                   subprocess.CompletedProcess([], 1, '', 'password=private')):
            with self.assertRaises(EvidenceError) as error:
                azure_json(['account', 'show'])
        self.assertNotIn('private', str(error.exception))

    def test_invalid_json_is_not_evidence(self):
        with patch('azure_classroom_preflight.subprocess.run', return_value=
                   subprocess.CompletedProcess([], 0, 'not json', '')):
            with self.assertRaises(EvidenceError):
                azure_json(['account', 'show'])

    def test_missing_cli_is_blocked(self):
        with patch('azure_classroom_preflight.shutil.which', return_value=None), patch('builtins.print') as output:
            self.assertEqual(main(['--subscription', 's', '--expected-sha', 'a' * 40]), 2)
        self.assertIn('BLOCKED', output.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
