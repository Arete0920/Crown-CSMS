"""Detect stale or malformed Linux/Python 3.12 backend dependency locks."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
METADATA = 'tools/ci/requirements-linux-py312.metadata.json'


def validate(root, metadata):
    errors = []
    expected = {'source': 'backend/requirements.txt',
                'lock': 'tools/ci/requirements-linux-py312.lock'}
    if metadata.get('schema_version') != 1 or metadata.get('platform') != 'linux' or metadata.get('python') != '3.12':
        errors.append('unsupported lock metadata schema or target')
    for kind, path in expected.items():
        if metadata.get(kind) != path:
            errors.append(f'unexpected {kind} path')
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if metadata.get(kind + '_sha256') != actual:
            errors.append(f'{kind} hash mismatch: regenerate lock and metadata together')
    text = (root / expected['lock']).read_text()
    records = text.replace('\\\n', '').splitlines()
    names = set()
    for record in records:
        if not record.strip() or record.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([^\s;]+)\s+((?:--hash=sha256:[0-9a-f]{64}\s*)+)', record.strip())
        if not match:
            errors.append('every locked requirement must use one exact version and SHA256 hashes')
            continue
        name = re.sub(r'[-_.]+', '-', match[1]).lower()
        if name in names:
            errors.append(f'duplicate locked package: {name}')
        names.add(name)
    if not names:
        errors.append('empty dependency lock')
    for line in (root / expected['source']).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        match = re.match(r'^([A-Za-z0-9_.-]+)', line)
        if not match or re.sub(r'[-_.]+', '-', match[1]).lower() not in names:
            errors.append(f'manifest dependency missing from lock: {line}')
    return errors


def main():
    try:
        errors = validate(ROOT, json.loads((ROOT / METADATA).read_text()))
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    if errors:
        print('\n'.join(errors))
        return 1
    print('PASS: Linux/Python 3.12 backend lock hashes, exact pins and manifest membership')
    return 0


if __name__ == '__main__':
    sys.exit(main())
