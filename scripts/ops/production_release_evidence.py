"""Bind recovery to verified deployed identities, never a workflow checkout SHA."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

SCHEMA = 1
WORKFLOWS = {'.github/workflows/deploy-prod.yml', '.github/workflows/deploy-prod-dispatch.yml'}
SHA = re.compile(r'[0-9a-f]{40}')
DIGEST = re.compile(r'sha256:[0-9a-f]{64}')
MAX_BYTES = 1024 * 1024
WORKFLOW_NAMES = {'Production Deploy', 'Production Deploy (Dispatch v2)'}


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamp must have timezone')
    return result


def validate_manifest(data, run, repository, app, registry, image):
    """Validate provenance, target boundary, health, and exact configured digest."""
    if run.get('status') != 'completed' or run.get('conclusion') != 'success':
        raise ValueError('Source run is not terminal-success')
    if run.get('path', '').split('@')[0] not in WORKFLOWS:
        raise ValueError('Source workflow is not allowlisted')
    source_repo = run.get('head_repository', {}).get('full_name')
    if source_repo != repository:
        raise ValueError('Source repository mismatch')
    if data.get('schema') != SCHEMA or data.get('repository') != repository:
        raise ValueError('Evidence schema or repository mismatch')
    if data.get('run_id') != run['id'] or data.get('run_attempt') != run['run_attempt']:
        raise ValueError('Evidence run/attempt mismatch')
    if data.get('workflow_source_sha') != run.get('head_sha'):
        raise ValueError('Workflow source binding mismatch')
    if data.get('webapp') != app or data.get('registry') != registry or data.get('image_name') != image:
        raise ValueError('Production target mismatch')
    sha, digest = data.get('deployed_sha', ''), data.get('image_digest', '')
    if not SHA.fullmatch(sha) or not DIGEST.fullmatch(digest):
        raise ValueError('Invalid deployed SHA or digest')
    expected_image = f'{registry}/{image}@{digest}'
    if data.get('configured_image') != expected_image:
        raise ValueError('Configured image does not match proven digest')
    tag, version, workflow_name = data.get('release_tag', ''), data.get('app_version', ''), data.get('deploy_workflow', '')
    if not re.fullmatch(r'prod-deploy-[A-Za-z0-9._-]+', tag) \
            or not re.fullmatch(r'[A-Za-z0-9._+-]{1,128}', version) or workflow_name not in WORKFLOW_NAMES:
        raise ValueError('Invalid release metadata')
    health = data.get('health', {})
    if health.get('ok') is not True or health.get('db') != 'ok' or health.get('env') != 'prod':
        raise ValueError('Database/runtime health not verified')
    if health.get('build_sha') != sha:
        raise ValueError('Live SHA differs from deployed SHA')
    if health.get('prod_deploy_tag') != tag or health.get('version') != version \
            or str(health.get('deploy_run_id')) != str(run['id']) or health.get('deploy_workflow') != workflow_name:
        raise ValueError('Live release metadata mismatch')
    verified = instant(data['verified_at'])
    if not instant(run['created_at']) <= verified <= instant(run['updated_at']):
        raise ValueError('Verification timestamp outside source run')
    return {'rollback_sha': sha, 'image_digest': digest, 'image_ref': expected_image,
            'release_tag': tag, 'app_version': version, 'deploy_workflow': workflow_name,
            'source_run_id': str(run['id']),
            'source_run_url': f"https://github.com/{repository}/actions/runs/{run['id']}"}


def unpack_manifest(payload):
    if len(payload) > MAX_BYTES:
        raise ValueError('Evidence archive is too large')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        rows = archive.infolist()
        if len(rows) != 1 or rows[0].filename != 'production-release-proof.json':
            raise ValueError('Unexpected evidence archive entries')
        if rows[0].file_size > 32768:
            raise ValueError('Evidence manifest is too large')
        return json.loads(archive.read(rows[0]))


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != 'https':
            raise ValueError('Artifact redirect must use HTTPS')
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if urlparse(newurl).hostname != 'api.github.com':
            result.remove_header('Authorization')
        return result


class GitHub:
    def __init__(self, repository, token):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid repository')
        self.base = f'https://api.github.com/repos/{repository}'
        self.token = token
        self.opener = build_opener(SafeRedirect())

    def get(self, path, binary=False):
        request = Request(self.base + path, headers={
            'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'})
        with self.opener.open(request, timeout=30) as response:
            payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError('GitHub response exceeds bounded evidence size')
        return payload if binary else json.loads(payload)


def resolve_target(api, failed, repository, app, registry, image):
    """Only completed, prior, successful deploys with exact-attempt proof qualify."""
    candidates = []
    for workflow in sorted(WORKFLOWS):
        name = workflow.rsplit('/', 1)[1]
        latest = api.get(f'/actions/workflows/{name}/runs?per_page=100')['workflow_runs']
        if any(run['id'] != failed['id'] and instant(run['created_at']) > instant(failed['created_at'])
               for run in latest):
            raise ValueError('Failed attempt has been superseded by a newer production attempt')
        for page in range(1, 4):
            runs = api.get(f'/actions/workflows/{name}/runs?status=success&per_page=100&page={page}')['workflow_runs']
            for run in runs:
                if run['id'] != failed['id'] and instant(run['updated_at']) < instant(failed['created_at']):
                    candidates.append(run)
            if len(runs) < 100:
                break
    for run in sorted(candidates, key=lambda row: row['updated_at'], reverse=True)[:40]:
        artifact_name = f"production-release-proof-{run['id']}-{run['run_attempt']}"
        artifacts = []
        for page in range(1, 4):
            rows = api.get(f"/actions/runs/{run['id']}/artifacts?per_page=100&page={page}")['artifacts']
            artifacts.extend(row for row in rows if row['name'] == artifact_name and not row['expired'])
            if len(rows) < 100:
                break
        if len(artifacts) != 1:
            continue
        artifact = artifacts[0]
        if artifact.get('workflow_run', {}).get('id') != run['id']:
            raise ValueError('Artifact origin mismatch')
        manifest = unpack_manifest(api.get(f"/actions/artifacts/{artifact['id']}/zip", binary=True))
        target = validate_manifest(manifest, run, repository, app, registry, image)
        target['source_artifact_id'] = str(artifact['id'])
        return target
    raise ValueError('No prior successful deployment has retained verified identity/digest evidence')


def record(env):
    health = json.loads(env['RESPONSE_JSON'])
    sha, image_ref = env['EXPECTED_SHA'], env['EXPECTED_IMAGE']
    registry, tail = image_ref.split('/', 1)
    image, digest = tail.rsplit('@', 1)
    if not SHA.fullmatch(sha) or not DIGEST.fullmatch(digest):
        raise ValueError('Invalid production release identity')
    configured = env['CONFIGURED_IMAGE']
    tag, version, workflow_name = env['DEPLOY_TAG'], env['APP_VERSION'], env['GITHUB_WORKFLOW']
    if not re.fullmatch(r'prod-deploy-[A-Za-z0-9._-]+', tag) \
            or not re.fullmatch(r'[A-Za-z0-9._+-]{1,128}', version) or workflow_name not in WORKFLOW_NAMES:
        raise ValueError('Invalid release metadata')
    if health.get('prod_deploy_tag') != tag or health.get('version') != version \
            or str(health.get('deploy_run_id')) != env['GITHUB_RUN_ID'] or health.get('deploy_workflow') != workflow_name:
        raise ValueError('Live release metadata mismatch')
    if configured != image_ref or health.get('ok') is not True or health.get('db') != 'ok' \
            or health.get('env') != 'prod' or health.get('build_sha') != sha:
        raise ValueError('Release proof requires exact configured image and healthy runtime SHA')
    return {'schema': SCHEMA, 'repository': env['GITHUB_REPOSITORY'],
            'run_id': int(env['GITHUB_RUN_ID']), 'run_attempt': int(env['GITHUB_RUN_ATTEMPT']),
            'workflow_source_sha': env['GITHUB_SHA'], 'webapp': env['WEBAPP_NAME'],
            'registry': registry, 'image_name': image, 'deployed_sha': sha, 'image_digest': digest,
            'release_tag': tag, 'app_version': version, 'deploy_workflow': workflow_name,
            'configured_image': configured, 'verified_at': datetime.now(timezone.utc).isoformat(),
            'health': {key: health[key] for key in ('ok', 'db', 'env', 'build_sha', 'prod_deploy_tag', 'version', 'deploy_run_id', 'deploy_workflow')}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['record', 'resolve'])
    args = parser.parse_args()
    if args.mode == 'record':
        path = Path('production-release-evidence/production-release-proof.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record(os.environ), indent=2) + '\n')
    else:
        env = os.environ
        api = GitHub(env['GITHUB_REPOSITORY'], env['GH_TOKEN'])
        failed = api.get(f"/actions/runs/{env['FAILED_RUN_ID']}")
        if failed.get('run_attempt') != int(env['FAILED_RUN_ATTEMPT']) \
                or failed.get('head_sha') != env['FAILED_RUN_SHA'] \
                or failed.get('created_at') != env['FAILED_RUN_CREATED_AT']:
            raise ValueError('Failed source run binding mismatch')
        target = resolve_target(api, failed, env['GITHUB_REPOSITORY'], env['WEBAPP_NAME'],
                                env['REGISTRY'], env['IMAGE_NAME'])
        with open(env['GITHUB_OUTPUT'], 'a') as output:
            for key, value in target.items():
                output.write(f'{key}={value}\n')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Never echo credential-bearing requests, redirects, or provider error bodies.
        raise SystemExit(f'Production release evidence blocked ({type(exc).__name__})') from None
