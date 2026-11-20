"""Offline safety contracts for the optional observability settings patcher."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).with_name("patch_observability_settings.py")
INITIAL = "MIDDLEWARE = [\n    'django.contrib.auth.middleware.AuthenticationMiddleware',\n]\n"


class ObservabilitySettingsTests(unittest.TestCase):
    def fixture(self, root: Path):
        script = root / "scripts" / "release" / "patch_observability_settings.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE, script)
        target = root / "backend" / "crown_api" / "settings.py"
        target.parent.mkdir(parents=True)
        target.write_text(INITIAL, encoding="utf-8")
        return script, target

    def run_script(self, script: Path, cwd: Path):
        return subprocess.run([sys.executable, str(script)], cwd=cwd, capture_output=True, text=True, check=False)

    def test_normal_run_and_repeat_are_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script, target = self.fixture(root)
            a = self.run_script(script, root)
            self.assertEqual(a.returncode, 0, a.stderr)
            after = target.read_text(encoding="utf-8")
            self.assertIn('"core.observability.middleware.RequestCorrelationMiddleware"', after)
            self.assertIn('"crown.request"', after)
            b = self.run_script(script, root)
            self.assertEqual(b.returncode, 0, b.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), after)

    def test_untrusted_working_directory_cannot_redirect_output(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as other:
            root = Path(folder)
            rogue = Path(other)
            script, target = self.fixture(root)
            rogue_target = rogue / "backend" / "crown_api" / "settings.py"
            rogue_target.parent.mkdir(parents=True)
            rogue_target.write_text("DO_NOT_TOUCH", encoding="utf-8")
            a = self.run_script(script, rogue)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(rogue_target.read_text(encoding="utf-8"), "DO_NOT_TOUCH")
            self.assertIn('"crown.request"', target.read_text(encoding="utf-8"))

    def test_linked_settings_file_and_parent_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as other:
            root = Path(folder)
            script, target = self.fixture(root)
            external = Path(other) / "external.py"
            external.write_text("DO_NOT_TOUCH", encoding="utf-8")
            target.unlink()
            try:
                target.symlink_to(external)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unsupported on this platform")
            self.assertNotEqual(self.run_script(script, root).returncode, 0)
            self.assertEqual(external.read_text(encoding="utf-8"), "DO_NOT_TOUCH")
            target.unlink()
            shutil.rmtree(target.parent)
            target.parent.symlink_to(Path(other), target_is_directory=True)
            self.assertNotEqual(self.run_script(script, root).returncode, 0)
            self.assertEqual(external.read_text(encoding="utf-8"), "DO_NOT_TOUCH")

    def test_directory_and_hardlinked_targets_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as other:
            root = Path(folder)
            script, target = self.fixture(root)
            target.unlink()
            target.mkdir()
            self.assertNotEqual(self.run_script(script, root).returncode, 0)
            target.rmdir()
            external = Path(other) / "external.py"
            external.write_text("DO_NOT_TOUCH", encoding="utf-8")
            try:
                os.link(external, target)
            except (OSError, NotImplementedError):
                self.skipTest("hardlinks unsupported")
            self.assertNotEqual(self.run_script(script, root).returncode, 0)
            self.assertEqual(external.read_text(encoding="utf-8"), "DO_NOT_TOUCH")

if __name__ == "__main__":
    unittest.main()
