"""Hermetic authority/receipt/plan tests; never contacts Azure or PostgreSQL."""
import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage_dev_heritage_graph as stage

SHA = 'a' * 40
RUN = '42238301088'
ENV = {
    'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
    'GITHUB_REF': 'refs/heads/main', 'GITHUB_SHA': SHA, 'GITHUB_RUN_ID': RUN,
}


def receipt():
    return {
        'result': 'PASS', 'source_sha': SHA, 'source_app': 'crown-api-dev',
        'data_origin': 'owner_attested_synthetic_dev',
        'source_write_performed': False, 'source_tls_verified': True,
        'source_transaction_read_only': True,
        'source_postgres_version': 150019,
        'source_database_identity_sha256': 'c'*64,
        'row_counts_match': True, 'column_definitions_match': True,
        'migration_history_match': True, 'backup_size_bytes': 2499919,
        'backup_sha256': 'd'*64,
        'disposable_database_created': True,
        'disposable_database_dropped': True,
        'ephemeral_backup_removed': True,
        'migration_rehearsal_requested': True,
        'application_rollback_compatibility': 'NOT_TESTED',
        'migration_rehearsal': {
            'result': 'PASS', 'source_sha': SHA, 'target_postgres_major': 15,
            'reviewed_migrations': 21, 'remaining_pending': 0,
            'existing_seed_rows_preserved': True,
            'existing_nonseed_table_values_preserved': True,
            'existing_table_counts_preserved': True, 'atomic_graph': True,
            'legacy_inserts_preserved': True, 'live_schema_write_performed': False,
            'baseline_migration_records': 245, 'migrated_records': 266,
            'baseline_public_tables': 467, 'baseline_fingerprint': 'b' * 64,
        },
    }

class StageContractTests(unittest.TestCase):
    def test_required_manual_main_dev_synthetic_backup_and_run(self):
        self.assertEqual(stage.authority(SHA, stage.CONFIRMATION, 'true', 'true', 'true', RUN, ENV), int(RUN))
        for key, value in [('GITHUB_ACTIONS', 'false'), ('GITHUB_REF', 'refs/heads/dev'),
                           ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_SHA', 'f'*40),
                           ('GITHUB_RUN_ID', '40000000000')]:
            with self.subTest(key=key), self.assertRaises(stage.StageBlocked):
                stage.authority(SHA, stage.CONFIRMATION, 'true', 'true', 'true', RUN, dict(ENV, **{key: value}))
        for kwargs in [(SHA, '', 'true', 'true', 'true', RUN),
                       (SHA, stage.CONFIRMATION, 'false', 'true', 'true', RUN),
                       (SHA, stage.CONFIRMATION, 'true', 'false', 'true', RUN),
                       (SHA, stage.CONFIRMATION, 'true', 'true', 'false', RUN),
                       (SHA, stage.CONFIRMATION, 'true', 'true', 'true', '0'),
                       ('not-sha', stage.CONFIRMATION, 'true', 'true', 'true', RUN)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(stage.StageBlocked):
                stage.authority(*kwargs, ENV)

    def test_rehearsal_receipt_is_exact_and_never_claims_rollback(self):
        self.assertTrue(stage.receipt_contract(receipt(), SHA))
        baseline = receipt()
        paths = [
            ('result', 'BLOCKED'), ('source_sha', 'c'*40), ('source_app', 'crown-api-prod'),
            ('data_origin', 'NOT_VERIFIED'), ('source_write_performed', True),
            ('source_tls_verified', False), ('source_transaction_read_only', False),
            ('source_postgres_version', 160000), ('backup_sha256', 'invalid'),
            ('row_counts_match', False), ('backup_size_bytes', 0),
            ('source_database_identity_sha256', 'invalid'),
            ('disposable_database_created', False),
            ('disposable_database_dropped', False), ('ephemeral_backup_removed', False),
            ('migration_rehearsal_requested', False), ('application_rollback_compatibility', 'PASS'),
        ]
        for key, value in paths:
            with self.subTest(key=key):
                bad = copy.deepcopy(baseline)
                bad[key] = value
                with self.assertRaises(stage.StageBlocked):
                    stage.receipt_contract(bad, SHA)
        for key, value in [
            ('result', 'BLOCKED'), ('source_sha', 'c'*40), ('reviewed_migrations', 20),
            ('reviewed_migrations', True), ('remaining_pending', 1),
            ('target_postgres_major', 16), ('atomic_graph', False),
            ('existing_seed_rows_preserved', False),
            ('existing_nonseed_table_values_preserved', False),
            ('existing_table_counts_preserved', False),
            ('legacy_inserts_preserved', False), ('live_schema_write_performed', True),
            ('migrated_records', 265), ('baseline_fingerprint', 'invalid'),
        ]:
            with self.subTest(key=key):
                bad = copy.deepcopy(baseline)
                bad['migration_rehearsal'][key] = value
                with self.assertRaises(stage.StageBlocked):
                    stage.receipt_contract(bad, SHA)

    def test_only_entire_forward_21_item_graph_can_write(self):
        reviewed = [f'app{i:02}.0001' for i in range(21)]
        plan = [(SimpleNamespace(app_label=f'app{i:02}', name='0001'), False)
                for i in range(21)]
        self.assertEqual(set(stage.plan_contract(plan, reviewed)), set(reviewed))
        for modified in (plan[:-1], list(reversed(plan[:-1])) + [plan[0]],
                         plan[:1] + [(plan[1][0], True)] + plan[2:],
                         plan[:-1] + [(SimpleNamespace(app_label='unreviewed', name='0001'), False)]):
            with self.assertRaises(stage.StageBlocked):
                stage.plan_contract(modified, reviewed)

    def test_main_is_verified_at_time_of_write(self):
        expected = [SimpleNamespace(returncode=0, stdout=SHA+'\n'),
                    SimpleNamespace(returncode=0, stdout=''),
                    SimpleNamespace(returncode=0, stdout=SHA+'\n')]
        runner=Mock(side_effect=expected)
        stage.verify_current_main(SHA, run=runner)
        self.assertEqual(runner.call_count, 3)
        for key, value in [(0, SimpleNamespace(returncode=0, stdout='b'*40)),
                           (1, SimpleNamespace(returncode=1, stdout='')),
                           (2, SimpleNamespace(returncode=0, stdout='c'*40))]:
            with self.subTest(key=key), self.assertRaises(stage.StageBlocked):
                bad=list(expected)
                bad[key]=value
                stage.verify_current_main(SHA, run=Mock(side_effect=bad))

    def test_cli_rejects_without_action_authority_before_reading_receipt(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'false'}, clear=True), \
             patch.object(stage.Path, 'open', side_effect=AssertionError('must not read')):
            import io
            from contextlib import redirect_stdout
            output=io.StringIO()
            with redirect_stdout(output):
                code=stage.main(['--expected-sha', SHA, '--rehearsal-receipt', '/invalid/path'])
            self.assertEqual(code,1)
            self.assertEqual(json.loads(output.getvalue())['result'],'BLOCKED')

if __name__ == '__main__':
    unittest.main()
