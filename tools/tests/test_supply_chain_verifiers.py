#!/usr/bin/env python3
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load_tool(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


dependency_admission = load_tool("verify_dependency_admission")
license_policy = load_tool("verify_license_policy")


class SupplyChainVerifierRejectionTests(unittest.TestCase):
    def test_dependency_admission_rejects_unapproved_direct_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requirements = root / "backend" / "requirements.txt"
            register = root / "docs" / "security" / "dependency-admissions.json"
            requirements.parent.mkdir(parents=True)
            register.parent.mkdir(parents=True)
            requirements.write_text("requests==2.32.5\n", encoding="utf-8")
            register.write_text(
                json.dumps({"schema_version": 1, "admissions": []}),
                encoding="utf-8",
            )

            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "CROWN verifier test"], cwd=root, check=True)
            subprocess.run(["git", "add", "backend/requirements.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)
            base_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()

            requirements.write_text(
                "requests==2.32.5\nunapproved-direct-dependency==1.0.0\n",
                encoding="utf-8",
            )

            output = io.StringIO()
            previous_cwd = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch.object(
                        dependency_admission,
                        "MANIFESTS",
                        [("backend/requirements.txt", "python")],
                    ),
                    patch.object(dependency_admission, "REGISTER", register),
                    patch.dict(os.environ, {"CROWN_BASE_SHA": base_sha}, clear=False),
                    redirect_stdout(output),
                ):
                    with self.assertRaises(SystemExit) as raised:
                        dependency_admission.main()
            finally:
                os.chdir(previous_cwd)

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("unapproved-direct-dependency", output.getvalue())

    def test_license_policy_rejects_blocked_license(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "licenses.json"
            report.write_text(
                json.dumps(
                    {
                        "unsafe-package@1.0.0": {
                            "licenses": "AGPL-3.0-only",
                        }
                    }
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with (
                patch.object(sys, "argv", ["verify_license_policy.py", str(report)]),
                redirect_stdout(output),
            ):
                with self.assertRaises(SystemExit) as raised:
                    license_policy.main()

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("blocked license", output.getvalue())
            self.assertIn("unsafe-package@1.0.0", output.getvalue())


if __name__ == "__main__":
    unittest.main()
