"""Hermetic authority/receipt/plan tests; never contacts Azure or PostgreSQL."""
import copy
import hashlib
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
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
RUN = '42273955790'
STAGE_RUN = '42280000000'
ARTIFACT_ID = '13532038006'
ENV = {
    'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
    'GITHUB_REF': 'refs/heads/main', 'GITHUB_SHA': SHA,
    'GITHUB_RUN_ID': STAGE_RUN, 'GITHUB_REPOSITORY': stage.REPO,
    'GITHUB_REPOSITORY_ID': str(stage.REPO_ID),
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
            'reviewed_migrations': 24, 'remaining_pending': 0,
            'existing_seed_rows_preserved': True,
            'existing_nonseed_table_values_preserved': True,
            'existing_table_counts_preserved': True, 'atomic_graph': True,
            'legacy_inserts_preserved': True, 'live_schema_write_performed': False,
            'baseline_migration_records': 245, 'migrated_records': 269,
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

    def test_prior_run_must_be_distinct_and_repository_pinned(self):
        self.assertEqual(stage.authority(
            SHA, stage.CONFIRMATION, 'true', 'true', 'true', RUN, ENV,
        ), int(RUN))
        for rejected_run in (STAGE_RUN, str(int(STAGE_RUN) + 1), '0', 'invalid'):
            with self.subTest(rejected_run=rejected_run), self.assertRaises(stage.StageBlocked):
                stage.authority(SHA, stage.CONFIRMATION, 'true', 'true', 'true',
                                rejected_run, ENV)
        for key, value in (
            ('GITHUB_REPOSITORY', 'other/project'),
            ('GITHUB_REPOSITORY_ID', '999'),
            ('GITHUB_RUN_ID', RUN),
        ):
            with self.subTest(key=key), self.assertRaises(stage.StageBlocked):
                stage.authority(SHA, stage.CONFIRMATION, 'true', 'true', 'true',
                                RUN, dict(ENV, **{key: value}))

    def test_github_rest_token_is_never_forwarded_by_redirect(self):
        class JsonResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self, limit):
                return b'{"accepted":true}'

        opener = Mock()
        opener.open.return_value = JsonResponse()
        # NoRedirect must refuse every status/code, including cross-origin 302.
        redirect = stage._NoRedirect()
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                self.assertIsNone(redirect.redirect_request(
                    None, None, status, 'redirect', {}, 'https://untrusted.example/evidence'
                ))
        with patch.object(stage, 'build_opener', return_value=opener) as make_opener, \
             patch.object(stage, 'urlopen', side_effect=AssertionError('must not use default opener')):
            response = stage._github_api_json('runs/' + RUN, 'ghs_testonly')
        self.assertEqual(response, {'accepted': True})
        self.assertIsInstance(make_opener.call_args.args[0], stage._NoRedirect)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url,
                         'https://api.github.com/repos/' + stage.REPO + '/actions/runs/' + RUN)
        self.assertEqual(request.get_header('Authorization'), 'Bearer ghs_testonly')

    def test_authenticated_prior_rehearsal_archive_accepts_exact_github_proof(self):
        stream = BytesIO()
        with ZipFile(stream, 'w', compression=ZIP_DEFLATED) as z:
            z.writestr(stage.REHEARSAL_RECEIPT_NAME, json.dumps(receipt()))
        archive = stream.getvalue()
        digest = 'sha256:' + hashlib.sha256(archive).hexdigest()
        run = {
            'id': int(RUN), 'status': 'completed', 'conclusion': 'success',
            'event': 'workflow_dispatch', 'head_branch': 'main', 'head_sha': SHA,
            'path': stage.REHEARSAL_WORKFLOW + '@refs/heads/main',
            'repository': {'id': stage.REPO_ID, 'full_name': stage.REPO},
            'head_repository': {'id': stage.REPO_ID},
        }
        artifact = {
            'id': int(ARTIFACT_ID), 'name': 'dev-operational-restore-' + RUN,
            'expired': False, 'size_in_bytes': len(archive), 'digest': digest,
            'workflow_run': {
                'id': int(RUN), 'repository_id': stage.REPO_ID,
                'head_repository_id': stage.REPO_ID, 'head_branch': 'main',
                'head_sha': SHA,
            },
        }
        inventory = {'total_count': 1, 'artifacts': [artifact]}
        env = dict(ENV, CROWN_STAGE_GITHUB_TOKEN='ghs_testonly')
        with patch.object(stage, '_github_api_json', side_effect=[run, inventory]) as api, \
             patch.object(stage, '_fetch_artifact_zip', return_value=archive) as fetch:
            self.assertEqual(
                stage.authenticated_rehearsal_receipt(RUN, ARTIFACT_ID, SHA, env),
                receipt(),
            )
            self.assertEqual(api.call_count, 2)
            fetch.assert_called_once_with(ARTIFACT_ID, 'ghs_testonly')

        # Never use arbitrary local JSON, caller checksum, or metadata without
        # a successful authenticated Actions run and an authenticated ZIP hash.
        for key, invalid in (
            ('status', 'queued'),
            ('conclusion', 'failure'),
            ('event', 'push'),
            ('head_sha', 'c' * 40),
            ('path', '.github/workflows/unrelated.yml@main'),
            ('head_branch', 'other'),
        ):
            bad = copy.deepcopy(run)
            bad[key] = invalid
            with self.subTest(run_field=key), \
                 patch.object(stage, '_github_api_json', return_value=bad), \
                 patch.object(stage, '_fetch_artifact_zip') as fetch, \
                 self.assertRaises(stage.StageBlocked):
                stage.authenticated_rehearsal_receipt(RUN, ARTIFACT_ID, SHA, env)
                fetch.assert_not_called()
        for key, invalid in (
            ('digest', 'sha256:' + '0' * 64),
            ('id', int(ARTIFACT_ID) + 1),
            ('expired', True),
            ('name', 'unrelated'),
        ):
            bad_artifact = copy.deepcopy(artifact)
            bad_artifact[key] = invalid
            bad_inventory = {'total_count': 1, 'artifacts': [bad_artifact]}
            with self.subTest(artifact_field=key), \
                 patch.object(stage, '_github_api_json',
                              side_effect=[run, bad_inventory]), \
                 patch.object(stage, '_fetch_artifact_zip',
                              return_value=archive), \
                 self.assertRaises(stage.StageBlocked):
                stage.authenticated_rehearsal_receipt(RUN, ARTIFACT_ID, SHA, env)
        for archive_payload in (b'not-a-zip', archive + b'forged'):
            with self.subTest(archive_size=len(archive_payload)), \
                 patch.object(stage, '_github_api_json',
                              side_effect=[run, inventory]), \
                 patch.object(stage, '_fetch_artifact_zip',
                              return_value=archive_payload), \
                 self.assertRaises(stage.StageBlocked):
                stage.authenticated_rehearsal_receipt(RUN, ARTIFACT_ID, SHA, env)
        with patch.object(stage, '_github_api_json', side_effect=AssertionError('must not call')):
            with self.assertRaises(stage.StageBlocked):
                stage.authenticated_rehearsal_receipt(
                    RUN, ARTIFACT_ID, SHA, ENV,
                )

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

    def test_live_baseline_requires_exact_rehearsed_data_and_schema(self):
        baseline = receipt()
        self.assertTrue(stage.live_baseline_contract(
            baseline, 'b' * 64, 245, 467,
        ))
        for fingerprint, history, tables in [
            ('a' * 64, 245, 467),  # same graph, stale table/data contents
            ('b' * 64, 244, 467),  # changed migration-history count
            ('b' * 64, 246, 467),
            ('b' * 64, 245, 466),  # schema table count drift
            ('b' * 64, 245, 468),
            ('bad', 245, 467),
            ('b' * 64, True, 467),
            ('b' * 64, 245, True),
        ]:
            with self.subTest(fingerprint=fingerprint, history=history, tables=tables):
                with self.assertRaisesRegex(
                    stage.StageBlocked, 'live_dev_baseline_differs_from_rehearsal'
                ):
                    stage.live_baseline_contract(baseline, fingerprint, history, tables)
        self.assertRaises(stage.StageBlocked, stage.live_baseline_contract,
                          {'migration_rehearsal': None}, 'b' * 64, 245, 467)

    def test_only_entire_forward_24_item_graph_can_write(self):
        reviewed = [f'app{i:02}.0001' for i in range(24)]
        plan = [(SimpleNamespace(app_label=f'app{i:02}', name='0001'), False)
                for i in range(24)]
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
             patch.object(stage, '_github_api_json', side_effect=AssertionError('must not call')):
            import io
            from contextlib import redirect_stdout
            output=io.StringIO()
            with redirect_stdout(output):
                code=stage.main(['--expected-sha', SHA, '--rehearsal-artifact-id', ARTIFACT_ID])
            self.assertEqual(code,1)
            self.assertEqual(json.loads(output.getvalue())['result'],'BLOCKED')

if __name__ == '__main__':
    unittest.main()
