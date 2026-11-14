import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import regenerate_backend_lock as generator


class RegenerationSafetyTests(unittest.TestCase):
    def test_failed_resolution_preserves_lock_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'backend/requirements.txt'
            lock = root / 'tools/ci/requirements-linux-py312.lock'
            metadata = root / generator.METADATA
            source.parent.mkdir(parents=True)
            lock.parent.mkdir(parents=True)
            source.write_text('example==2\n')
            lock.write_text('previous lock\n')
            metadata.write_text(json.dumps({
                'compiler': 'pip-tools==7.6.2',
                'source': str(source.relative_to(root)),
                'lock': str(lock.relative_to(root)),
            }))
            before = metadata.read_bytes(), lock.read_bytes()
            with patch.object(generator, 'version', return_value='7.6.2'), patch.object(
                generator.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'compile')
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    generator.regenerate(root)
            self.assertEqual(before, (metadata.read_bytes(), lock.read_bytes()))

    def test_wrong_compiler_is_rejected_before_execution(self):
        with patch.object(generator, 'version', return_value='0.0.0'), patch.object(
            generator.subprocess, 'run'
        ) as run:
            with self.assertRaisesRegex(RuntimeError, 'exact compiler'):
                generator.regenerate()
            run.assert_not_called()
