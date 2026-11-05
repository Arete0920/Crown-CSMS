"""PR hygiene counts source changes even when CI checks out a merge commit."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

GATE = Path(__file__).resolve().parents[2] / 'scripts/ci/pr_hygiene_gate.py'
sys.path.insert(0, str(GATE.parent))
from pr_hygiene_gate import pr_language_findings
from repository_identity_hygiene import REFERENCE_WORDS, reference_found


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



@pytest.mark.parametrize('edited_count, expected_code', [(19, 0), (20, 1)])
def test_removed_path_is_included_in_source_file_limit(tmp_path, edited_count, expected_code):
    """A deletion is a changed path, even when other files are only modified."""
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Repository test')
    git(tmp_path, 'config', 'user.email', 'test@local.invalid')
    for index in range(21):
        (tmp_path / f'item_{index}.txt').write_text('original\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Base')
    base = git(tmp_path, 'rev-parse', 'HEAD')

    git(tmp_path, 'checkout', '-b', 'source')
    (tmp_path / 'item_0.txt').unlink()
    for index in range(1, edited_count + 1):
        (tmp_path / f'item_{index}.txt').write_text('modified\n')
    git(tmp_path, 'add', '-A')
    git(tmp_path, 'commit', '-m', 'Mixed deletion and edits')
    source = git(tmp_path, 'rev-parse', 'HEAD')

    event = tmp_path / 'event.json'
    event.write_text(json.dumps({
        'pull_request': {'head': {'sha': source}, 'title': 'File count check', 'body': ''}
    }))
    env = {**os.environ, 'CROWN_BASE_REF': base, 'GITHUB_EVENT_PATH': str(event),
           'CROWN_MAX_CHANGED_FILES': '20', 'CROWN_MAX_NORMAL_ADDITIONS': '1500'}
    result = subprocess.run(
        [sys.executable, str(GATE)], cwd=tmp_path, env=env, text=True, capture_output=True
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    assert f'changed_files={edited_count + 1}' in result.stdout
    assert 'D +0/-1 item_0.txt' in result.stdout
    if expected_code:
        assert 'changed file count 21 exceeds limit 20' in result.stdout
    else:
        assert 'PASS' in result.stdout



def test_deleting_legacy_generated_artifact_does_not_block_cleanup(tmp_path):
    """Deleted artifacts count as paths, not newly committed forbidden content."""
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Repository test')
    git(tmp_path, 'config', 'user.email', 'test@local.invalid')
    report = tmp_path / 'audit-artifacts' / 'old-run' / 'playwright-report' / 'trace.log'
    report.parent.mkdir(parents=True)
    report.write_text('historical output\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Historical artifact')
    base = git(tmp_path, 'rev-parse', 'HEAD')

    git(tmp_path, 'checkout', '-b', 'source')
    report.unlink()
    git(tmp_path, 'add', '-A')
    git(tmp_path, 'commit', '-m', 'Remove old report')
    source = git(tmp_path, 'rev-parse', 'HEAD')

    event = tmp_path / 'event.json'
    event.write_text(json.dumps({
        'pull_request': {'head': {'sha': source}, 'title': 'Remove stale report', 'body': ''}
    }))
    env = {**os.environ, 'CROWN_BASE_REF': base, 'GITHUB_EVENT_PATH': str(event),
           'CROWN_MAX_CHANGED_FILES': '20'}
    result = subprocess.run(
        [sys.executable, str(GATE)], cwd=tmp_path, env=env, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'changed_files=1' in result.stdout
    assert 'D +0/-1 audit-artifacts/old-run/playwright-report/trace.log' in result.stdout
    assert 'forbidden generated artifact' not in result.stdout
    assert 'timestamped/stale evidence path' not in result.stdout
    assert 'PASS' in result.stdout


@pytest.mark.parametrize('field', ['title', 'body'])
def test_pr_metadata_reference_denied_with_precise_field(field):
    metadata = {'title': 'Review school ledger', 'body': 'Verified data boundary'}
    metadata[field] = 'Prepared with ' + REFERENCE_WORDS[0]
    findings = pr_language_findings(metadata)
    assert len(findings) == 1
    assert f'pull-request {field} at line(s) 1' in findings[0]


def test_pr_metadata_wrapped_reference_and_neutral_narrative():
    wrapped = next(
        word for word in REFERENCE_WORDS
        if ' ' in word and all(not reference_found(piece) for piece in word.split())
    )
    findings = pr_language_findings({'body': 'Technical review\n' + wrapped.replace(' ', '\n')})
    assert findings == ['prohibited wrapped reference in pull-request body']
    assert pr_language_findings({'title': 'Verify account isolation', 'body': 'Evidence pending, release not authorized.'}) == []
    assert pr_language_findings({'title': None, 'body': None}) == []


def test_pr_metadata_guard_integrated_in_source_head_gate(tmp_path):
    git(tmp_path, 'init', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Repository test')
    git(tmp_path, 'config', 'user.email', 'test@local.invalid')
    (tmp_path / 'source.py').write_text('value = 1\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Base')
    base = git(tmp_path, 'rev-parse', 'HEAD')
    git(tmp_path, 'checkout', '-b', 'source')
    (tmp_path / 'source.py').write_text('value = 2\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Source change')
    source = git(tmp_path, 'rev-parse', 'HEAD')
    event = tmp_path / 'event.json'
    env = {**os.environ, 'CROWN_BASE_REF': base, 'GITHUB_EVENT_PATH': str(event)}
    event.write_text(json.dumps({'pull_request': {'head': {'sha': source},
                           'title': 'Review school ledger',
                           'body': 'Prepared with ' + REFERENCE_WORDS[0]}}))
    denied = subprocess.run([sys.executable, str(GATE)], cwd=tmp_path,
                            env=env, text=True, capture_output=True)
    assert denied.returncode == 1
    assert 'prohibited reference in pull-request body' in denied.stdout
    event.write_text(json.dumps({'pull_request': {'head': {'sha': source},
                           'title': 'Review school ledger',
                           'body': 'Verified data boundary'}}))
    accepted = subprocess.run([sys.executable, str(GATE)], cwd=tmp_path,
                              env=env, text=True, capture_output=True)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
