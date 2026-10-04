"""PR hygiene counts source changes even when CI checks out a merge commit."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

GATE = Path(__file__).resolve().parents[2] / 'scripts/ci/pr_hygiene_gate.py'


def git(directory, *args):
    return subprocess.check_output(['git', *args], cwd=directory, text=True, stderr=subprocess.DEVNULL).strip()


@pytest.mark.parametrize('source_count, expected_code', [(1, 0), (21, 1)])
def test_merge_checkout_excludes_base_noise_but_enforces_source_limit(tmp_path, source_count, expected_code):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Repository test')
    git(tmp_path, 'config', 'user.email', 'test@local.invalid')
    (tmp_path / 'base.py').write_text('base = True\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    git(tmp_path, 'checkout', '-b', 'source')
    for index in range(source_count):
        (tmp_path / f'source_{index}.py').write_text('source = True\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Source change')
    source = git(tmp_path, 'rev-parse', 'HEAD')
    git(tmp_path, 'checkout', 'main')
    for index in range(25):
        (tmp_path / f'independent_{index}.py').write_text('independent = True\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Independent base changes')
    git(tmp_path, 'checkout', 'source')
    git(tmp_path, 'merge', '--no-edit', 'main')
    event = tmp_path / 'event.json'
    event.write_text(json.dumps({'pull_request': {'head': {'sha': source}, 'body': ''}}))
    env = {**os.environ, 'CROWN_BASE_REF': base, 'GITHUB_EVENT_PATH': str(event),
           'CROWN_MAX_CHANGED_FILES': '20', 'CROWN_MAX_NORMAL_ADDITIONS': '1500'}
    result = subprocess.run([sys.executable, str(GATE)], cwd=tmp_path, env=env, text=True, capture_output=True)
    assert result.returncode == expected_code, result.stdout + result.stderr
    if source_count > 20:
        assert 'changed file count 21 exceeds limit 20' in result.stdout
    else:
        assert 'PASS' in result.stdout
    # A malformed PR event cannot fall back to the synthetic merge checkout.
    event.write_text(json.dumps({'pull_request': {'head': {}, 'body': ''}}))
    denied = subprocess.run([sys.executable, str(GATE)], cwd=tmp_path, env=env, text=True, capture_output=True)
    assert denied.returncode == 1
    assert 'requires an exact source head SHA' in denied.stdout
