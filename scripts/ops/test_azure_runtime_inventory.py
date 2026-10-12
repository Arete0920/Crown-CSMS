"""Read-only runtime evidence privacy and failure contracts; no Azure calls."""
import io
import json
from pathlib import Path
import unittest
import urllib.error

import azure_runtime_inventory as inventory
from crown_azure_cost_audit import ReadUnavailable


class Response(io.BytesIO):
    status = 200


class RuntimeInventoryTests(unittest.TestCase):
    def fake(self, *cmd):
        self.commands.append(cmd)
        if cmd[:2] == ('webapp', 'list'):
            return ['crown-api-prod', 'possible-worker']
        if cmd[:3] == ('webapp', 'config', 'show'):
            return {'alwaysOn': True, 'image': 'DOCKER|crownregistry.azurecr.io/crown2026:abc',
                    'healthCheckPath': '/api/health/', 'appCommandLine': 'PRIVATE'}
        if cmd[:3] == ('webapp', 'config', 'appsettings'):
            return ['CELERY_BROKER_URL', 'DATABASE_URL']
        if cmd[:3] == ('acr', 'repository', 'show'):
            return {'digest': 'sha256:' + '1' * 64, 'PRIVATE': 'SECRET'}
        return [{'name': 'crown-db-prod', 'retentionDays': 7, 'geoRedundant': 'Disabled',
                 'earliestRestoreDate': '2026-10-10T00:00:00Z'}]

    def setUp(self):
        self.commands = []

    def test_projected_inventory_and_registry_digest_are_read_only(self):
        packet = inventory.collect('crown-rg', 'crown-api-prod', read=self.fake,
                                   health_read=lambda app: {'status': 'UNAVAILABLE'})
        self.assertEqual(len(packet['webapps']), 2)
        self.assertEqual(packet['release_status'], 'NOT VERIFIED')
        self.assertNotIn('PRIVATE', json.dumps(packet))
        self.assertEqual(packet['webapps'][0]['registry_manifest']['data']['digest'], 'sha256:' + '1' * 64)
        for cmd in self.commands:
            self.assertIn('--query', cmd)
            self.assertNotIn('set', cmd)
            self.assertNotIn('create', cmd)
            self.assertNotIn('update', cmd)
            if cmd[:3] == ('webapp', 'config', 'appsettings'):
                self.assertEqual(cmd[-1], '[].name')

    def test_read_denial_does_not_become_empty_or_healthy(self):
        def denied(*cmd):
            raise ReadUnavailable('PRIVATE', 'ACCESS_DENIED')
        packet = inventory.collect('crown-rg', 'crown-api-prod', read=denied,
                                   health_read=lambda app: {'status': 'UNAVAILABLE'})
        self.assertEqual(packet['webapp_listing_status'], 'UNAVAILABLE')
        self.assertEqual(packet['postgres_backup_metadata']['status'], 'UNAVAILABLE')
        self.assertNotIn('PRIVATE', json.dumps(packet))

    def test_raw_configuration_values_are_rejected(self):
        def malformed(*cmd):
            if cmd[:3] == ('webapp', 'config', 'appsettings'):
                return [{'name': 'DATABASE_URL', 'value': 'PRIVATE'}]
            if cmd[:3] == ('postgres', 'flexible-server', 'list'):
                return [{'administratorLoginPassword': 'PRIVATE'}]
            return self.fake(*cmd)
        packet = inventory.collect('crown-rg', 'crown-api-prod', read=malformed,
                                   health_read=lambda app: {})
        self.assertEqual(packet['webapps'][0]['setting_names']['status'], 'UNAVAILABLE')
        self.assertEqual(packet['postgres_backup_metadata']['status'], 'UNAVAILABLE')
        self.assertNotIn('PRIVATE', json.dumps(packet))

    def test_health_retains_only_valid_sha_and_database_state(self):
        body = {'build_sha': 'a' * 40, 'db': 'ok', 'secret': 'PRIVATE'}
        def open_url(url, timeout):
            self.assertEqual(url, 'https://crown-api-prod.azurewebsites.net/api/health/')
            self.assertEqual(timeout, 20)
            return Response(json.dumps(body).encode())
        packet = inventory.health('crown-api-prod', open_url)
        self.assertEqual(packet['build_sha'], 'a' * 40)
        self.assertEqual(packet['database'], 'ok')
        self.assertNotIn('PRIVATE', json.dumps(packet))

    def test_http_200_is_not_database_success(self):
        packet = inventory.health('crown-api-prod', lambda *a, **k: Response(b'{"db":"error","build_sha":"PRIVATE"}'))
        self.assertEqual(packet['database'], 'error')
        self.assertIsNone(packet['build_sha'])

    def test_failed_and_oversized_health_reads_are_unknown(self):
        def denied(*a, **k):
            raise urllib.error.HTTPError('PRIVATE', 403, 'PRIVATE', {}, None)
        self.assertEqual(inventory.health('crown-api-prod', denied), {'status': 'UNAVAILABLE', 'http_status': 403})
        self.assertEqual(inventory.health('crown-api-prod', lambda *a, **k: Response(b'x' * 65537))['status'], 'UNAVAILABLE')
        self.assertIsNone(inventory.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))

    def test_invalid_targets_are_rejected_before_requests(self):
        with self.assertRaises(ValueError):
            inventory.health('https://PRIVATE')
        with self.assertRaises(ValueError):
            inventory.collect('--bad', 'crown-api-prod', read=self.fake)
        self.assertFalse(self.commands)

    def test_runtime_collection_keeps_manual_main_guard(self):
        workflow = (Path(__file__).resolve().parents[2] / '.github/workflows/azure-classroom-preflight.yml').read_text()
        self.assertIn("if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'", workflow)
        self.assertIn('test_azure_runtime_inventory.py', workflow)
        self.assertIn('azure-runtime-inventory.json', workflow)


if __name__ == '__main__':
    unittest.main()
