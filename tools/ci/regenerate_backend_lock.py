"""Resolve and validate the Linux/Python 3.12 lock before updating its metadata."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from verify_backend_lock import validate

ROOT = Path(__file__).resolve().parents[2]
METADATA = Path('tools/ci/requirements-linux-py312.metadata.json')


def regenerate(root=ROOT):
    metadata = json.loads((root / METADATA).read_text())
    if sys.platform != 'linux' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('Use Linux with Python 3.12; Windows needs a separate lock')
    if metadata['compiler'] != 'pip-tools==' + version('pip-tools'):
        raise RuntimeError('Install the exact compiler recorded in lock metadata')
    source, lock = Path(metadata['source']), Path(metadata['lock'])
    source_bytes = (root / source).read_bytes()
    with tempfile.TemporaryDirectory(prefix='crown-lock-') as directory:
        stage = Path(directory)
        for path in (source, lock):
            (stage / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, stage / path)
        # Seed with existing pins so unrelated dependencies are not upgraded.
        subprocess.run([
            sys.executable, '-m', 'piptools', 'compile', '--generate-hashes',
            '--no-emit-index-url', '--no-emit-trusted-host', '--no-header',
            '--no-annotate', '--output-file', str(lock), str(source),
        ], cwd=stage, check=True)
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--dry-run',
            '--ignore-installed', '--require-hashes', '--only-binary=:all:',
            '-r', str(lock),
        ], cwd=stage, check=True)
        metadata['source_sha256'] = hashlib.sha256(source_bytes).hexdigest()
        metadata['lock_sha256'] = hashlib.sha256((stage / lock).read_bytes()).hexdigest()
        errors = validate(stage, metadata)
        if errors:
            raise RuntimeError('; '.join(errors))
        if (root / source).read_bytes() != source_bytes:
            raise RuntimeError('Requirements changed during resolution; retry on a stable source')
        # No repository output changes until resolution and hash installation pass.
        (root / lock).write_bytes((stage / lock).read_bytes())
        (root / METADATA).write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    regenerate()
