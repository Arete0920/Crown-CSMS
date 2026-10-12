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
            {'alwaysOn': True}, {'id': 'plan'}, ['DATABASE_URL', 'CELERY_BROKER_URL'], [],
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
            ['webapp', 'config'], ['webapp', 'config'],
        ])
        self.assertTrue(all('--query' in call for call in calls))

    def test_stopped_app_is_observed_without_mutation(self):
        responses = iter(self.inventory('Stopped'))
        result = collect('subscription', 'group', 'app', 'a' * 40, lambda _: next(responses))
        self.assertEqual(result['api']['state'], 'Stopped')
        self.assertEqual(result['release_status'], 'NOT VERIFIED')

    def test_configuration_collects_names_without_values(self):
        responses = iter(self.inventory())
        calls = []
        def read(args):
            calls.append(args)
            return next(responses)
        result = collect('subscription', 'group', 'app', 'a' * 40, read)
        self.assertEqual(result['configuration']['app_setting_names'],
                         {'status': 'COLLECTED', 'names': ['CELERY_BROKER_URL', 'DATABASE_URL']})
        self.assertEqual(result['configuration']['connection_string_names']['names'], [])
        for call in calls[-2:]:
            self.assertEqual(call[call.index('--query') + 1], '[].name')
        self.assertEqual(calls[-2][:4], ['webapp', 'config', 'appsettings', 'list'])
        self.assertEqual(calls[-1][:4], ['webapp', 'config', 'connection-string', 'list'])

    def test_configuration_denied_is_not_an_empty_inventory(self):
        responses = iter(self.inventory()[:5])
        def read(args):
            if args[:4] in (['webapp', 'config', 'appsettings', 'list'],
                             ['webapp', 'config', 'connection-string', 'list']):
                raise EvidenceError('password=private')
            return next(responses)
        result = collect('subscription', 'group', 'app', 'a' * 40, read)
        for item in result['configuration'].values():
            self.assertEqual(item, {'status': 'UNAVAILABLE', 'names': None})
        self.assertNotIn('private', str(result))
        self.assertEqual(result['release_status'], 'NOT VERIFIED')

    def test_unexpected_raw_settings_never_leak_values(self):
        responses = iter(self.inventory()[:5] + [
            [{'name': 'DATABASE_URL', 'value': 'password=private'}],
            {'DATABASE_URL': 'password=private'},
        ])
        result = collect('subscription', 'group', 'app', 'a' * 40, lambda _: next(responses))
        self.assertNotIn('private', str(result))
        self.assertTrue(all(item['status'] == 'UNAVAILABLE'
                            for item in result['configuration'].values()))

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
