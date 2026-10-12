#!/usr/bin/env python3
"""Read-only hosted configuration evidence; collection is not release acceptance."""
import argparse
from datetime import datetime, timezone
import json
import re
import urllib.error
import urllib.request

from crown_azure_cost_audit import ReadUnavailable, az_json

NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9-]{0,62}')
SHA = re.compile(r'[0-9a-f]{40}')
IMAGE = re.compile(r'DOCKER\|([a-z0-9]+)\.azurecr\.io/([a-z0-9./_-]+(?::[A-Za-z0-9_.-]+|@sha256:[0-9a-f]{64}))')


def optional_read(*parts, read=az_json):
    try:
        return {'status': 'COLLECTED', 'data': read(*parts)}
    except ReadUnavailable as exc:
        return {'status': 'UNAVAILABLE', 'category': exc.category, 'data': None}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def health(app, open_url=None):
    if not NAME.fullmatch(app):
        raise ValueError('Invalid Azure app name.')
    opener = open_url or urllib.request.build_opener(NoRedirect()).open
    try:
        with opener(f'https://{app}.azurewebsites.net/api/health/', timeout=20) as response:
            body = response.read(65537)
            if len(body) > 65536:
                raise ValueError('Oversized health response.')
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError('Unexpected health response.')
            sha = data.get('build_sha')
            return {'status': 'COLLECTED', 'http_status': response.status,
                    'build_sha': sha if isinstance(sha, str) and SHA.fullmatch(sha) else None,
                    'database': data.get('db') if data.get('db') in ('ok', 'error', 'unreachable') else 'UNKNOWN'}
    except urllib.error.HTTPError as exc:
        return {'status': 'UNAVAILABLE', 'http_status': exc.code}
    except (OSError, ValueError, urllib.error.URLError):
        return {'status': 'UNAVAILABLE', 'http_status': None}


def collect(group, api, read=az_json, health_read=health):
    if not NAME.fullmatch(group) or not NAME.fullmatch(api):
        raise ValueError('Invalid Azure target name.')
    common = ('--resource-group', group)
    apps = optional_read('webapp', 'list', *common, '--query', '[].name', read=read)
    app_packets = []
    if apps['status'] == 'COLLECTED':
        names = apps['data']
        if not isinstance(names, list) or not all(isinstance(n, str) and NAME.fullmatch(n) for n in names):
            apps = {'status': 'UNAVAILABLE', 'data': None}
        else:
            for name in sorted(set(names)):
                config = optional_read('webapp', 'config', 'show', *common, '--name', name,
                    '--query', '{alwaysOn:alwaysOn,image:linuxFxVersion,healthCheckPath:healthCheckPath}', read=read)
                settings = optional_read('webapp', 'config', 'appsettings', 'list', *common,
                    '--name', name, '--query', '[].name', read=read)
                if settings['status'] == 'COLLECTED':
                    rows = settings['data']
                    settings = ({'status': 'COLLECTED', 'data': sorted(set(rows))}
                        if isinstance(rows, list) and all(isinstance(n, str) for n in rows)
                        else {'status': 'UNAVAILABLE', 'data': None})
                # Retain only whitelisted projected configuration; never startup commands.
                raw = config['data']
                if config['status'] == 'COLLECTED' and isinstance(raw, dict):
                    image = raw.get('image')
                    match = IMAGE.fullmatch(image) if isinstance(image, str) else None
                    path = raw.get('healthCheckPath')
                    config['data'] = {'alwaysOn': raw.get('alwaysOn') if isinstance(raw.get('alwaysOn'), bool) else None,
                        'image': image if match else None,
                        'healthCheckPath': path if isinstance(path, str) and re.fullmatch(r'/[A-Za-z0-9/_-]*', path) else None}
                    manifest = (optional_read('acr', 'repository', 'show', '--name', match[1],
                        '--image', match[2], '--query', '{digest:digest}', read=read)
                        if match else {'status': 'UNAVAILABLE', 'data': None})
                    digest = manifest['data']
                    if manifest['status'] == 'COLLECTED':
                        manifest = ({'status': 'COLLECTED', 'data': {'digest': digest['digest']}}
                            if isinstance(digest, dict) and isinstance(digest.get('digest'), str)
                            and re.fullmatch(r'sha256:[0-9a-f]{64}', digest['digest'])
                            else {'status': 'UNAVAILABLE', 'data': None})
                else:
                    config = {'status': 'UNAVAILABLE', 'data': None}
                    manifest = {'status': 'UNAVAILABLE', 'data': None}
                app_packets.append({'name': name, 'configuration': config,
                                    'setting_names': settings, 'registry_manifest': manifest})
    backups = optional_read('postgres', 'flexible-server', 'list', *common, '--query',
        '[].{name:name,retentionDays:backup.backupRetentionDays,geoRedundant:backup.geoRedundantBackup,earliestRestoreDate:backup.earliestRestoreDate}', read=read)
    if backups['status'] == 'COLLECTED':
        rows = backups['data']
        fields = {'name', 'retentionDays', 'geoRedundant', 'earliestRestoreDate'}
        if not isinstance(rows, list) or not all(isinstance(row, dict) and set(row) <= fields
                and all(value is None or isinstance(value, (str, int)) for value in row.values()) for row in rows):
            backups = {'status': 'UNAVAILABLE', 'data': None}
    return {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
            'release_status': 'NOT VERIFIED', 'webapp_listing_status': apps['status'],
            'webapps': app_packets, 'api_health': health_read(api), 'postgres_backup_metadata': backups,
            'limits': ['Setting names do not prove values or broker connectivity.',
                       'Web app listings do not discover processes inside VMs or external services.',
                       'Health database probe does not prove migrations or tenant acceptance.',
                       'Backup metadata does not prove a successful restore or accepted RTO/RPO.',
                       'Registry digest resolution does not prove the running container digest.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource-group', default='crown-rg')
    parser.add_argument('--api-app', default='crown-api-prod')
    args = parser.parse_args()
    print(json.dumps(collect(args.resource_group, args.api_app), indent=2))


if __name__ == '__main__':
    main()
