"""Synthetic immutable recovery evidence: no cloud access or production mutations."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
from urllib.request import Request
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('production_release_evidence',
                                            ROOT / 'scripts/ops/production_release_evidence.py')
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)
SHA = 'a' * 40
SOURCE_SHA = 'b' * 40
DIGEST = 'sha256:' + 'c' * 64
REPO = 'owner/repository'
IMAGE = f'registry.example/image@{DIGEST}'


def source_run(run_id=7):
    return dict(id=run_id, run_attempt=2, status='completed', conclusion='success',
                path='.github/workflows/deploy-prod-dispatch.yml', head_sha=SOURCE_SHA,
                head_repository={'full_name': REPO}, created_at='2026-10-01T00:00:00Z',
                updated_at='2026-10-01T00:10:00Z', html_url=f'https://github.com/{REPO}/actions/runs/{run_id}')


def manifest():
    return dict(schema=1, repository=REPO, run_id=7, run_attempt=2, workflow_source_sha=SOURCE_SHA,
                webapp='app', registry='registry.example', image_name='image', deployed_sha=SHA,
                image_digest=DIGEST, configured_image=IMAGE, verified_at='2026-10-01T00:09:00Z',
                release_tag='prod-deploy-proof', app_version='crown-0.4.0', deploy_workflow='Production Deploy (Dispatch v2)',
                health={'ok': True, 'db': 'ok', 'env': 'prod', 'build_sha': SHA,
                        'prod_deploy_tag': 'prod-deploy-proof', 'version': 'crown-0.4.0',
                        'deploy_run_id': '7', 'deploy_workflow': 'Production Deploy (Dispatch v2)'})


def archive(data):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as output:
        output.writestr('production-release-proof.json', json.dumps(data))
    return buffer.getvalue()


class FakeAPI:
    def __init__(self, runs=None, artifacts=None, data=None):
        self.runs = [source_run()] if runs is None else runs
        self.artifacts = [dict(id=9, name='production-release-proof-7-2', expired=False,
                               workflow_run={'id': 7})] if artifacts is None else artifacts
        self.data = manifest() if data is None else data
        self.calls = []
        self.latest = []

    def get(self, path, binary=False):
        self.calls.append(path)
        if '/workflows/' in path and 'status=success' not in path:
            return {'workflow_runs': self.latest}
        if '/workflows/deploy-prod-dispatch.yml/runs' in path:
            return {'workflow_runs': self.runs}
        if '/workflows/deploy-prod.yml/runs' in path:
            return {'workflow_runs': []}
        if '/artifacts?' in path:
            return {'artifacts': self.artifacts}
        if '/artifacts/9/zip' in path and binary:
            return archive(self.data)
        raise AssertionError(f'Unexpected API path {path}')


class ProductionReleaseEvidenceTests(unittest.TestCase):
    def validate(self, data=None, run=None):
        return evidence.validate_manifest(data or manifest(), run or source_run(), REPO,
                                          'app', 'registry.example', 'image')

    def resolve(self, api):
        return evidence.resolve_target(api, {'id': 10, 'created_at': '2026-10-02T00:00:00Z'},
                                       REPO, 'app', 'registry.example', 'image')

    def test_dispatch_deployed_sha_is_distinct_from_workflow_sha(self):
        result = self.resolve(FakeAPI())
        self.assertEqual(result['rollback_sha'], SHA)
        self.assertNotEqual(result['rollback_sha'], SOURCE_SHA)
        self.assertEqual(result['image_ref'], IMAGE)
        self.assertEqual(result['source_artifact_id'], '9')

    def test_manifest_rejects_mismatched_or_unhealthy_evidence(self):
        for change in [{'run_id': 8}, {'run_attempt': 1}, {'workflow_source_sha': SHA},
                       {'repository': 'foreign/repository'}, {'webapp': 'foreign-app'},
                       {'image_digest': 'latest'}, {'deployed_sha': 'short'},
                       {'configured_image': f'registry.example/image:{SHA}'},
                       {'release_tag': 'bad\noutput'}, {'app_version': 'bad\noutput'},
                       {'verified_at': '2026-10-02T00:00:00Z'}, {'schema': 0}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate({**manifest(), **change})
        for change in [{'ok': False}, {'db': 'failed'}, {'env': 'dev'}, {'build_sha': SOURCE_SHA}, {'deploy_run_id': '99'},
                       {'prod_deploy_tag': 'wrong'}, {'version': 'wrong'}, {'deploy_workflow': 'wrong'}]:
            data = manifest()
            data['health'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(data)

    def test_successful_workflow_without_proof_is_not_a_rollback_target(self):
        for artifacts in [[], [dict(id=9, name='production-release-proof-7-1', expired=False)],
                          [dict(id=9, name='production-release-proof-7-2', expired=True)]]:
            with self.subTest(artifacts=artifacts), self.assertRaises(ValueError):
                self.resolve(FakeAPI(artifacts=artifacts))

    def test_foreign_failed_or_untrusted_source_run_rejected(self):
        for change in [{'conclusion': 'failure'}, {'status': 'in_progress'},
                       {'path': '.github/workflows/untrusted.yml'},
                       {'head_repository': {'full_name': 'foreign/repository'}}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(run={**source_run(), **change})

    def test_future_or_same_run_never_used(self):
        for change in [{'id': 10}, {'updated_at': '2026-10-03T00:00:00Z'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.resolve(FakeAPI(runs=[{**source_run(), **change}]))

    def test_superseded_failure_cannot_choose_a_rollback_target(self):
        api = FakeAPI()
        api.latest = [{**source_run(11), 'created_at': '2026-10-03T00:00:00Z'}]
        with self.assertRaisesRegex(ValueError, 'superseded'):
            self.resolve(api)

    def test_production_image_mutations_share_concurrency_and_approval(self):
        for name in ['deploy-prod.yml', 'deploy-prod-dispatch.yml',
                     'prod-rollback-on-failure.yml', 'prod-immutable-rollback-drill.yml']:
            workflow = yaml.safe_load((ROOT / '.github/workflows' / name).read_text())
            self.assertEqual(workflow['concurrency']['group'], 'crown-api-prod-deploy')
            self.assertFalse(workflow['concurrency']['cancel-in-progress'])
        recovery = yaml.safe_load((ROOT / '.github/workflows/prod-rollback-on-failure.yml').read_text())
        self.assertEqual(recovery['jobs']['rollback']['environment'], 'production')

    def test_duplicate_artifacts_and_origin_mismatch_fail_closed(self):
        api = FakeAPI()
        api.artifacts *= 2
        with self.assertRaises(ValueError):
            self.resolve(api)
        api = FakeAPI()
        api.artifacts[0]['workflow_run']['id'] = 99
        with self.assertRaises(ValueError):
            self.resolve(api)

    def test_archive_never_extracts_paths_and_rejects_extra_entries(self):
        self.assertEqual(evidence.unpack_manifest(archive(manifest())), manifest())
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as output:
            output.writestr('../production-release-proof.json', '{}')
        with self.assertRaises(ValueError):
            evidence.unpack_manifest(buffer.getvalue())
        with self.assertRaises(ValueError):
            evidence.unpack_manifest(b'x' * (evidence.MAX_BYTES + 1))

    def test_redirect_does_not_forward_github_token(self):
        request = Request('https://api.github.com/example', headers={'Authorization': 'Bearer test'})
        redirected = evidence.SafeRedirect().redirect_request(request, None, 302, 'Found', {},
                                                              'https://artifact.example/file')
        self.assertIsNone(redirected.get_header('Authorization'))
        with self.assertRaises(ValueError):
            evidence.SafeRedirect().redirect_request(request, None, 302, 'Found', {}, 'http://example/file')

    def test_record_requires_healthy_exact_configured_digest(self):
        env = dict(RESPONSE_JSON=json.dumps(manifest()['health']), EXPECTED_SHA=SHA,
                   EXPECTED_IMAGE=IMAGE, CONFIGURED_IMAGE=IMAGE, GITHUB_REPOSITORY=REPO,
                   GITHUB_RUN_ID='7', GITHUB_RUN_ATTEMPT='2', GITHUB_SHA=SOURCE_SHA, WEBAPP_NAME='app',
                   DEPLOY_TAG='prod-deploy-proof', APP_VERSION='crown-0.4.0', GITHUB_WORKFLOW='Production Deploy (Dispatch v2)')
        row = evidence.record(env)
        self.assertEqual(row['deployed_sha'], SHA)
        self.assertEqual(row['workflow_source_sha'], SOURCE_SHA)
        self.assertEqual(set(row['health']), set(manifest()['health']))
        with self.assertRaises(ValueError):
            evidence.record({**env, 'CONFIGURED_IMAGE': IMAGE.replace('@', ':')})

    def test_actual_identity_steps_execute_and_emit_dispatch_safe_proof(self):
        import os
        import shutil
        import subprocess
        import tempfile
        for name in ['deploy-prod.yml', 'deploy-prod-dispatch.yml']:
            workflow = yaml.safe_load((ROOT / '.github/workflows' / name).read_text())
            step = next(row for row in workflow['jobs']['build-and-deploy']['steps']
                        if row['name'] == 'Verify release identity end-to-end')
            if name == 'deploy-prod.yml':
                self.assertEqual(step['env']['DEPLOY_TAG'], '${{ needs.resolve-release.outputs.deploy_tag }}')
            else:
                self.assertIn('DEPLOY_TAG', workflow['jobs']['build-and-deploy']['env'])
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'scripts/ops').mkdir(parents=True)
                shutil.copy(ROOT / 'scripts/ops/production_release_evidence.py', root / 'scripts/ops')
                (root / 'VERSION').write_text('crown-0.4.0\n')
                env = dict(os.environ, EXPECTED_SHA=SHA, EXPECTED_IMAGE=IMAGE,
                           DEPLOY_TAG='prod-deploy-proof', GITHUB_REPOSITORY=REPO,
                           GITHUB_RUN_ID='7', GITHUB_RUN_ATTEMPT='2', GITHUB_SHA=SOURCE_SHA,
                           GITHUB_WORKFLOW='Production Deploy (Dispatch v2)', WEBAPP_NAME='app',
                           MOCK_IMAGE=IMAGE, MOCK_HEALTH=json.dumps(manifest()['health']))
                script = 'az() { printf "%s\\n" "$MOCK_IMAGE"; }; curl() { printf "%s\\n" "$MOCK_HEALTH"; };\n' + step['run']
                result = subprocess.run(['bash', '-c', script], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads((root / 'production-release-evidence/production-release-proof.json').read_text())
                self.assertEqual(data['deployed_sha'], SHA)
                self.assertEqual(data['workflow_source_sha'], SOURCE_SHA)
                self.assertEqual(data['image_digest'], DIGEST)
                # A failed transfer can still produce parseable partial JSON; it is not proof.
                proof = root / 'production-release-evidence/production-release-proof.json'
                proof.unlink()
                bad = 'az() { printf "%s\\n" "$MOCK_IMAGE"; }; curl() { printf "%s\\n" "$MOCK_HEALTH"; return 1; }; sleep() { :; };\n' + step['run']
                failed = subprocess.run(['bash', '-c', bad], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=20)
                self.assertNotEqual(failed.returncode, 0)
                self.assertFalse(proof.exists())


    def test_actual_workflows_retain_evidence_only_after_identity_verification(self):
        for name in ['deploy-prod.yml', 'deploy-prod-dispatch.yml']:
            steps = yaml.safe_load((ROOT / '.github/workflows' / name).read_text())['jobs']['build-and-deploy']['steps']
            names = [step['name'] for step in steps]
            self.assertLess(names.index('Verify release identity end-to-end'),
                            names.index('Retain verified production release identity'))
            verify = next(step for step in steps if step['name'] == 'Verify release identity end-to-end')
            self.assertIn('production_release_evidence.py record', verify['run'])
            self.assertIn('HEALTH_FETCHED=true', verify['run'])
            self.assertIn('\"$HEALTH_FETCHED\" != \"true\"', verify['run'])
            retain = next(step for step in steps if step['name'] == 'Retain verified production release identity')
            self.assertEqual(retain['with']['if-no-files-found'], 'error')
            self.assertEqual(retain['with']['retention-days'], 30)
            self.assertNotIn('always()', retain.get('if', ''))
        workflow = yaml.safe_load((ROOT / '.github/workflows/prod-rollback-on-failure.yml').read_text())
        steps = workflow['jobs']['rollback']['steps']
        target = next(step for step in steps if step.get('id') == 'rollback_target')
        self.assertIn('production_release_evidence.py resolve', target['run'])
        self.assertNotIn('.head_sha', target['run'])
        restore = next(step for step in steps if step.get('id') == 'restore')
        self.assertIn('--image "$IMAGE_NAME@$IMAGE_DIGEST"', restore['run'])
        self.assertNotIn('IMAGE_REF="$REGISTRY/$IMAGE_NAME:$ROLLBACK_SHA"', restore['run'])
        verify = next(step for step in steps if step.get('id') == 'verify')
        self.assertIn('Restored configured digest mismatch', verify['run'])
        self.assertIn('rm -f /tmp/rollback_health.json', verify['run'])
        self.assertIn('"$LIVE_SHA" == "$ROLLBACK_SHA"', verify['run'])


if __name__ == '__main__':
    unittest.main()
