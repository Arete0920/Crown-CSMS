import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('backend_lock', Path(__file__).with_name('verify_backend_lock.py'))
lock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lock)


class BackendLockTests(unittest.TestCase):
    def check(self, manifest='sample>=1\n', contents=None, stale=False):
        if contents is None:
            contents = 'sample==1.2 --hash=sha256:' + 'a' * 64 + '\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = {'schema_version': 1, 'platform': 'linux', 'python': '3.12'}
            for kind, path, data in [('source', 'backend/requirements.txt', manifest),
                                     ('lock', 'tools/ci/requirements-linux-py312.lock', contents)]:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(data)
                metadata[kind] = path
                metadata[kind + '_sha256'] = hashlib.sha256(data.encode()).hexdigest()
            if stale:
                metadata['source_sha256'] = 'b' * 64
            return lock.validate(root, metadata)

    def test_hashed_exact_lock_passes(self):
        self.assertEqual(self.check(), [])

    def test_stale_manifest_is_rejected(self):
        self.assertTrue(self.check(stale=True))

    def test_missing_manifest_package_is_rejected(self):
        self.assertTrue(self.check(manifest='missing>=1\n'))

    def test_floating_or_unhashed_requirements_are_rejected(self):
        for contents in ['sample>=1 --hash=sha256:' + 'a' * 64, 'sample==1.2', '--index-url https://example.invalid']:
            with self.subTest(contents=contents):
                self.assertTrue(self.check(contents=contents))

    def test_duplicate_package_is_rejected(self):
        self.assertTrue(self.check(contents=('sample==1.2 --hash=sha256:' + 'a' * 64 + '\n') * 2))


if __name__ == '__main__':
    unittest.main()
