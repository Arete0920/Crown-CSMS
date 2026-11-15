"""Explicit loopback-only compiled UI acceptance with independent DB persistence checks."""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import pytest
from sandbox_demo.test_universal_access import operator_secrets
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_identity import presenter_username
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_care import prepare_presenter_care
from sandbox_demo.universal_jireh import prepare_presenter_jireh


@pytest.mark.skipif(os.environ.get('CROWN_RUN_UNIVERSAL_BROWSER') != '1', reason='Explicit disposable local browser harness only')
@pytest.mark.django_db(transaction=True)
def test_actual_module_browser_transactions(live_server, local_runtime, operator_secrets, settings, tmp_path, monkeypatch):
    from django.core.management import call_command
    from io import StringIO
    from aid.models import AidApplication
    from aftercare.models import DaycareRelease, AftercareAttendance
    from jireh_sgo.models import SGOFamilyIntake
    from summer_camp.models import SummerCampEnrollment
    call_command('seed_permissions', stdout=StringIO())
    # A transactional test flush can remove migration-seeded safety grants.
    # A fresh test schema is required, never grant these ad hoc in this harness.
    root = Path(__file__).resolve().parents[2]
    front = root / 'frontend/dashboards'
    assert live_server.url == 'http://127.0.0.1:8004'
    settings.CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:4179']
    settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
    data = prepare_presenter(apply=True, enable_password_login=True)
    care = prepare_presenter_care(apply=True)
    prepare_presenter_jireh(apply=True)
    camp = SummerCampEnrollment.objects.get(school_id=data['school_id'])
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    monkeypatch.setenv('BUILD_SHA', source)
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip())
    fixture = {'synthetic': True, 'school_id': data['school_id'], 'source_sha': source, 'source_dirty': dirty,
        'care': care, 'camp_session_id': camp.session_id, 'api': live_server.url, 'frontend': 'http://127.0.0.1:4179',
        'usernames': {key: presenter_username(key) for key in operator_secrets}, 'passwords': operator_secrets}
    output = root / '.local-backups/universal-demo/module-browser-evidence.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    env = {**os.environ, 'CROWN_UNIVERSAL_BROWSER_FIXTURE': json.dumps(fixture), 'CROWN_UNIVERSAL_BROWSER_OUTPUT': str(output)}
    if Path('/usr/bin/chromium').exists():
        env['CROWN_BROWSER_EXECUTABLE'] = '/usr/bin/chromium'
    with (tmp_path / 'module-preview.log').open('w') as log:
        preview = subprocess.Popen(['node', 'node_modules/vite/bin/vite.js', 'preview', '--host', '127.0.0.1', '--port', '4179', '--strictPort'], cwd=front, stdout=log, stderr=log)
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen('http://127.0.0.1:4179/login', timeout=1).close()
                    break
                except OSError:
                    assert preview.poll() is None, 'Owned preview exited'
                    time.sleep(.1)
            else:
                pytest.fail('Owned preview did not become ready')
            result = subprocess.run(['node', 'scripts/universal-module-acceptance.mjs'], cwd=front, env=env, capture_output=True, text=True, timeout=240)
            assert preview.poll() is None, 'Owned preview exited'
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            preview.terminate()
            preview.wait(timeout=15)
    assert AidApplication.objects.get(school_id=data['school_id']).status == 'SUBMITTED'
    assert SGOFamilyIntake.objects.get().revision == 3
    assert DaycareRelease.objects.filter(school_id=data['school_id']).count() == 1
    rows = list(AftercareAttendance.objects.filter(school_fk_id=data['school_id']).order_by('care_session'))
    assert len(rows) == 2 and rows[0].handoff_verified and rows[1].pickup_verified
    camp.refresh_from_db()
    assert camp.readiness_status == 'BLOCKED'
