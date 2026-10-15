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



NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$")
MAX_FREE_SITES = 10

class AdmissionDenied(Exception):
    pass

def check_name(name):
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise AdmissionDenied("Invalid Azure name")
    return name

def tier(resource):
    if not isinstance(resource, dict):
        raise AdmissionDenied("Malformed Azure record")
    sku = resource.get("sku")
    if isinstance(sku, dict):
        sku = sku.get("name")
    if not isinstance(sku, str) or sku.lower() not in ("free", "standard", "dedicated"):
        raise AdmissionDenied("Unknown or unavailable SKU")
    return sku.lower()

def ownership(resource):
    rid = resource.get("id")
    if not isinstance(rid, str):
        raise AdmissionDenied("Missing Azure resource ID")
    match = re.search(r"/resourceGroups/([^/]+)/providers/Microsoft\.Web/staticSites/([^/]+)$", rid, re.I)
    if not match:
        raise AdmissionDenied("Unexpected Azure resource ownership ID")
    return match.group(1), match.group(2)

def plan(resources, name="jireh-site", group="crown-rg"):
    check_name(name)
    check_name(group)
    if not isinstance(resources, list) or len(resources) > 500:
        raise AdmissionDenied("Subscription inventory cannot be trusted")
    found = []
    free_count = 0
    for r in resources:
        if tier(r) == "free":
            free_count += 1
        owner_group, owner_name = ownership(r)
        if owner_name.lower() == name.lower():
            found.append((r, owner_group))
    if len(found) > 1:
        raise AdmissionDenied("Duplicate Jireh site identity")
    if found:
        resource, owner_group = found[0]
        if owner_group.lower() != group.lower() or tier(resource) != "free":
            raise AdmissionDenied("Jireh site belongs to another owner or paid tier")
        return "REUSE_VERIFIED_FREE"
    if free_count >= MAX_FREE_SITES:
        raise AdmissionDenied("No free-tier quota remains")
    return "CREATE_FREE"

def verify(resource, name="jireh-site", group="crown-rg"):
    check_name(name)
    check_name(group)
    owner_group, owner_name = ownership(resource)
    if tier(resource) != "free" or owner_group.lower() != group.lower() or owner_name.lower() != name.lower():
        raise AdmissionDenied("Post-provision resource is not isolated and free")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--inventory')
    modes.add_argument('--verify-resource')
    parser.add_argument('--name', default='jireh-site')
    parser.add_argument('--group', default='crown-rg')
    parser.add_argument('--resource-group', default='crown-rg')
    parser.add_argument('--output', default='jireh-azure-site-preflight.json')
    args = parser.parse_args()
    if args.inventory or args.verify_resource:
        try:
            with open(args.inventory or args.verify_resource, encoding='utf-8') as source:
                resource = json.load(source)
            if args.inventory:
                print(plan(resource, args.name, args.group))
            else:
                verify(resource, args.name, args.group)
                print('VERIFIED_FREE')
        except (AdmissionDenied, ValueError, OSError):
            raise SystemExit('BLOCKED: Azure Static Web Apps Free entitlement cannot be confirmed') from None
        return
    data = collect(args.resource_group)
    with open(args.output, 'w', encoding='utf-8') as target:
        json.dump(data, target, indent=2, sort_keys=True)
        target.write('\n')
    print('Jireh read-only checks: ' + str(data['checks'])
          + '; production release NOT AUTHORIZED.')


if __name__ == '__main__':
    main()
