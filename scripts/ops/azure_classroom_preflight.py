#!/usr/bin/env python3
"""Collect read-only Azure release inventory; never certify runtime readiness."""
import argparse
from datetime import datetime, timezone
import json
import re
import shutil
import subprocess
import sys


class EvidenceError(Exception):
    pass


def azure_json(arguments):
    try:
        result = subprocess.run(
            ['az', *arguments, '--output', 'json', '--only-show-errors'],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EvidenceError('Azure read failed or timed out; no runtime conclusion.') from exc
    # Do not echo CLI stderr, which can contain resource configuration or secrets.
    if result.returncode:
        raise EvidenceError('Azure read denied or unavailable; verify login and permissions.')
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise EvidenceError('Azure returned invalid JSON; evidence is unavailable.') from exc


def collect(subscription, group, app, sha, read=azure_json):
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise EvidenceError('Expected SHA must be a full lowercase commit SHA.')
    account = read(['account', 'show', '--subscription', subscription,
                    '--query', '{id:id,state:state}'])
    if account.get('id', '').lower() != subscription.lower() or account.get('state') != 'Enabled':
        raise EvidenceError('Selected Azure subscription is mismatched or disabled.')
    common = ['--subscription', subscription, '--resource-group', group]
    resources = read(['resource', 'list', *common, '--query',
                      '[].{id:id,name:name,type:type,location:location}'])
    web = read(['webapp', 'show', *common, '--name', app, '--query',
                '{id:id,name:name,state:state,host:defaultHostName,plan:serverFarmId}'])
    config = read(['webapp', 'config', 'show', *common, '--name', app, '--query',
                   '{alwaysOn:alwaysOn,linuxFxVersion:linuxFxVersion}'])
    if not web.get('id') or not web.get('plan'):
        raise EvidenceError('Web app or service plan identity is missing.')
    plan = read(['appservice', 'plan', 'show', '--subscription', subscription,
                 '--ids', web['plan'], '--query', '{id:id,sku:sku,location:location}'])
    # Resource inventory is presence evidence only, not broker/worker health.
    return {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'expected_sha': sha, 'subscription': account['id'], 'resource_group': group,
        'collection_status': 'COLLECTED', 'release_status': 'NOT VERIFIED',
        'resources': resources, 'api': web, 'api_config': config, 'plan': plan,
        'remaining_proofs': [
            'Immutable artifact and live API/frontend/worker/beat identity parity',
            'Controlled PostgreSQL migrations through academics 0048 with no pending migrations',
            'Hosted broker connectivity and registered worker task',
            'Beat publication matched to worker execution by task ID',
            'Digest and conference notice persistence, retries and duplicate suppression',
            'Hosted teacher/student/parent/admin/board acceptance and denied-access checks',
            'Monitoring, backup/restore and rollback acceptance',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subscription', required=True)
    parser.add_argument('--resource-group', default='crown-rg')
    parser.add_argument('--api-app', default='crown-api-prod')
    parser.add_argument('--expected-sha', required=True)
    args = parser.parse_args(argv)
    if not shutil.which('az'):
        print(json.dumps({'collection_status': 'BLOCKED', 'release_status': 'NOT VERIFIED',
                          'reason': 'Azure CLI is unavailable in this execution environment.'}))
        return 2
    try:
        packet = collect(args.subscription, args.resource_group, args.api_app, args.expected_sha)
    except EvidenceError as exc:
        print(json.dumps({'collection_status': 'BLOCKED', 'release_status': 'NOT VERIFIED',
                          'reason': str(exc)}))
        return 2
    print(json.dumps(packet, indent=2))
    return 0  # Collection success is explicitly not release acceptance.


if __name__ == '__main__':
    sys.exit(main())
