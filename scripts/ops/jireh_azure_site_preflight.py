#!/usr/bin/env python3
"""Read-only Azure hosting and cost-evidence preflight for the Jireh website."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import re
import subprocess

SAFE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$')


def command(parts):
    assert parts and parts[0] == 'az'
    done = subprocess.run(parts, capture_output=True, text=True, timeout=40, check=False)
    if done.returncode:
        return None
    try:
        return json.loads(done.stdout)
    except ValueError:
        return None


def collect(resource_group='crown-rg', *, run=command):
    if not SAFE.fullmatch(resource_group):
        raise ValueError('Invalid resource group')
    checks = {}
    account = run(['az', 'account', 'show', '--query', '{id:id,state:state}',
                   '-o', 'json', '--only-show-errors'])
    checks['subscription'] = ('COLLECTED' if isinstance(account, dict)
        and account.get('state') == 'Enabled' else 'UNAVAILABLE')
    apps = run(['az', 'staticwebapp', 'list', '--resource-group', resource_group,
                '-o', 'json', '--only-show-errors'])
    if isinstance(apps, list) and all(isinstance(v, dict) for v in apps):
        checks['static_web_apps'] = 'COLLECTED'
        sku = Counter()
        existing = []
        for app in apps:
            tier = (app.get('sku') or {}).get('name') if isinstance(app.get('sku'), dict) else None
            sku[tier if tier in ('Free', 'Standard') else 'UNKNOWN'] += 1
            if app.get('name') == 'jireh-site':
                existing.append('jireh-site')
        static = {'count': len(apps), 'sku_counts': dict(sorted(sku.items())),
                  'existing_jireh_site': bool(existing)}
    else:
        checks['static_web_apps'] = 'UNAVAILABLE'
        static = None
    budgets = run(['az', 'consumption', 'budget', 'list', '--resource-group',
                   resource_group, '-o', 'json', '--only-show-errors'])
    checks['resource_group_budgets'] = 'COLLECTED' if isinstance(budgets, list) else 'UNAVAILABLE'
    return {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'product': 'Jireh Financial Aid', 'read_only': True,
        'resource_group': resource_group, 'checks': checks, 'static_sites': static,
        'budget_count': len(budgets) if isinstance(budgets, list) else None,
        'actual_cost_status': 'NOT_COLLECTED', 'launch_authorized': False,
        'release_status': 'BLOCKED_PENDING_OWNER_COST_AND_DNS_EVIDENCE',
        'required_next': [
            'Owner verifies current and previous month actual Azure spend at subscription scope',
            'Owner verifies budget alerts; alerts are not a hard spend cap',
            'Owner approves any recurring charges before provisioning',
            'Azure staging TLS and site must pass functional browser tests with no live student data',
            'Back up authoritative DNS and MX/SPF/DKIM/DMARC before cutover',
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource-group', default='crown-rg')
    p.add_argument('--output', default='jireh-azure-site-preflight.json')
    a = p.parse_args()
    data = collect(a.resource_group)
    with open(a.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')
    print('Jireh read-only checks: ' + str(data['checks'])
          + '; production release NOT AUTHORIZED.')


if __name__ == '__main__':
    main()
