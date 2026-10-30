"""Synthetic, offline negative tests for privileged DEV reset execution authority."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ops/verify_dev_reset_authority.py"
WORKFLOWS = (
    ROOT / ".github/workflows/demo-reset.yml",
    ROOT / ".github/workflows/ops-reset-dev.yml",
)
SCHOOL = "19801b59-8c05-4c84-9312-5d792e4e839d"
OTHER = "b23f7d65-2d77-4d79-983f-6dbdb8abc345"
SHA = "a" * 40
STALE = "b" * 40


class ResetAuthorityTests(unittest.TestCase):
    def run_guard(self, **overrides):
        with tempfile.TemporaryDirectory() as d:
            fake_git = Path(d) / "git"
            fake_git.write_text(
                '#!/bin/sh\n'
                'if [ "$1" = "fetch" ]; then\n'
                '  if [ "$FAKE_FETCH_FAIL" = "yes" ]; then exit 3; fi\n'
                '  exit 0\n'
                'fi\n'
                'if [ "$1" = "rev-parse" ]; then\n'
                '  case "$2" in\n'
                '    HEAD) printf "%s\\n" "$FAKE_HEAD_SHA";;\n'
                '    refs/remotes/origin/main) printf "%s\\n" "$FAKE_MAIN_SHA";;\n'
                '    *) exit 4;;\n'
                '  esac\n'
                '  exit 0\n'
                'fi\n'
                'exit 5\n', encoding="utf-8",
            )
            fake_git.chmod(0o755)
            env = dict(
                os.environ,
                PATH=d + os.pathsep + os.environ.get("PATH", ""),
                GITHUB_REPOSITORY="Arete0920/Crown-CSMS",
                GITHUB_EVENT_NAME="workflow_dispatch",
                GITHUB_REF="refs/heads/main",
                GITHUB_REF_PROTECTED="true",
                GITHUB_RUN_ATTEMPT="1",
                GITHUB_SHA=SHA,
                SCHOOL_ID=SCHOOL,
                CONFIRM_SCHOOL_ID=SCHOOL,
                DEV_RESET_ALLOWED_SCHOOL_IDS=SCHOOL + ", " + OTHER,
                FAKE_HEAD_SHA=SHA,
                FAKE_MAIN_SHA=SHA,
                FAKE_FETCH_FAIL="no",
            )
            env.update(overrides)
            return subprocess.run(
                [sys.executable, str(SCRIPT)],
                env=env, cwd=d, capture_output=True, text=True, check=False, timeout=15,
            )

    def test_passes_only_exact_current_main_and_confirmed_allowlisted_uuid(self):
        outcome = self.run_guard()
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertIn("PASS", outcome.stdout)
        self.assertNotIn(SCHOOL, outcome.stdout)

    def test_fail_closed_cases(self):
        cases = [
            {"GITHUB_REPOSITORY": "fork/Crown-CSMS"},
            {"GITHUB_EVENT_NAME": "push"},
            {"GITHUB_REF": "refs/heads/rc/old"},
            {"GITHUB_REF_PROTECTED": "false"},
            {"GITHUB_RUN_ATTEMPT": "2"},
            {"GITHUB_SHA": "abcd"},
            {"GITHUB_SHA": STALE},
            {"FAKE_MAIN_SHA": STALE},
            {"FAKE_HEAD_SHA": STALE},
            {"FAKE_FETCH_FAIL": "yes"},
            {"SCHOOL_ID": OTHER},
            {"SCHOOL_ID": "not-a-uuid"},
            {"CONFIRM_SCHOOL_ID": OTHER},
            {"DEV_RESET_ALLOWED_SCHOOL_IDS": ""},
            {"DEV_RESET_ALLOWED_SCHOOL_IDS": OTHER},
            {"DEV_RESET_ALLOWED_SCHOOL_IDS": SCHOOL + ", bad"},
            {"DEV_RESET_ALLOWED_SCHOOL_IDS": SCHOOL + "," + SCHOOL},
            {"DEV_RESET_ALLOWED_SCHOOL_IDS": "00000000-0000-0000-0000-000000000000"},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                outcome = self.run_guard(**kwargs)
                self.assertEqual(outcome.returncode, 1, outcome.stdout + outcome.stderr)
                self.assertIn("BLOCKED", outcome.stderr)
                self.assertNotIn(SCHOOL, outcome.stderr)

    def test_workflows_check_authority_before_each_credentialed_request(self):
        # No PyYAML dependency: CI already discovers this file through pytest.ini.
        command = "python3 scripts/ops/verify_dev_reset_authority.py"
        for path in WORKFLOWS:
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIn("    environment: dev\n", source)
                self.assertIn("    concurrency:\n      group: crown-api-dev-deploy\n      cancel-in-progress: false", source)
                self.assertIn(
                    "    if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'",
                    source,
                )
                self.assertIn("permissions:\n  contents: read", source)
                self.assertIn("concurrency:\n  group: ops-reset-dev\n  cancel-in-progress: false", source)
                checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
                self.assertIn(checkout, source)
                self.assertIn("          ref: ${{ github.sha }}", source)
                self.assertLess(source.index(checkout), source.index("      - name: Verify current source"))
                self.assertIn(command, source)
                self.assertIn("      confirm_school_id:\n", source)
                self.assertIn("        required: true", source)
                self.assertIn("          DEV_RESET_ALLOWED_SCHOOL_IDS: ${{ vars.DEV_RESET_ALLOWED_SCHOOL_IDS }}", source)
                self.assertIn("          CONFIRM_SCHOOL_ID: ${{ inputs.confirm_school_id }}", source)
                credentialed_steps = 0
                for step in source.split("\n      - name: ")[1:]:
                    if "curl " in step:
                        credentialed_steps += 1
                        self.assertIn(command, step)
                        self.assertLess(step.index(command), step.index("curl "))
                        self.assertIn("          DEV_RESET_ALLOWED_SCHOOL_IDS: ${{ vars.DEV_RESET_ALLOWED_SCHOOL_IDS }}", step)
                        self.assertIn("          CONFIRM_SCHOOL_ID: ${{ inputs.confirm_school_id }}", step)
                        self.assertIn("          SCHOOL_ID: ${{ inputs.school_id }}", step)
                self.assertGreaterEqual(credentialed_steps, 1)


if __name__ == "__main__":
    unittest.main()
