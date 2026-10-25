"""Exercise the deployed-identity script offline and enforce mutation boundaries."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / '.github/workflows/deploy-dashboard.yml').read_text()
DEV = WORKFLOW.split('  dev-certification-preview:\n', 1)[1]
ORIGIN = 'https://yellow-forest-0eecc8b0f-devcertification.eastus2.7.azurestaticapps.net'
SHA = 'a' * 40


def step(name):
    match = re.search(r'^      - name: ' + re.escape(name) + r'\n(.*?)(?=^      - |\Z)', DEV, re.M | re.S)
    if not match:
        raise AssertionError('Missing workflow step: ' + name)
    return match.group(1)


class DeployOnlyBoundaryTests(unittest.TestCase):
    def test_deploy_only_defaults_to_true(self):
        self.assertRegex(WORKFLOW, r'dev_deploy_only:\n[^\n]*\n        type: boolean\n        default: true')

    def test_all_mutating_certification_steps_require_explicit_opt_in(self):
        names = [
            'Configure exact owned DEV preview origin',
            'Install existing Playwright browser',
            'Execute existing live certification against DEV preview',
            'Execute existing buyer persistence journeys on DEV',
            'Upload DEV buyer persistence evidence',
            'Set up existing backend fixture runtime',
            'Install accepted backend dependencies for synthetic fixtures',
            'Prepare two synthetic DEV tenants using existing models',
            'Execute existing Playwright framework for two-tenant HTTP isolation',
            'Upload two-tenant execution results',
        ]
        for name in names:
            with self.subTest(name=name):
                condition = re.search(r'^        if: (.*)$', step(name), re.M).group(1)
                self.assertIn("toJSON(inputs.dev_deploy_only) == 'false'", condition)
                # Evaluate the actual workflow condition for omitted/true/false input
                # and both preview outcomes; always() must not bypass the mode gate.
                for mode in (None, '', True, False):
                    for outcome in ('success', 'failure'):
                        expression = condition.replace('always()', 'True')
                        expression = expression.replace("toJSON(inputs.dev_deploy_only) == 'false'", str(json.dumps(mode) == 'false'))
                        expression = expression.replace("steps.preview.outcome == 'success'", str(outcome == 'success'))
                        clauses = [clause.strip() for clause in expression.split('&&')]
                        self.assertTrue(all(clause in ('True', 'False') for clause in clauses))
                        result = all(clause == 'True' for clause in clauses)
                        self.assertEqual(result, mode is False and (outcome == 'success' or 'steps.preview' not in condition))

    def test_read_only_checks_and_token_cleanup_remain_enabled(self):
        for name in ('Verify pinned DEV API and existing CORS', 'Verify deployed DEV frontend identity without writes'):
            self.assertNotIn('inputs.dev_deploy_only', step(name))
        self.assertIn('if: always()', step('Remove ephemeral synthetic actor tokens'))
        self.assertIn('does not certify tenant isolation or owner workflows', step('Record DEV deployment scope'))

    def test_exact_main_guard_accepts_only_fresh_main_and_rejects_stale_ancestor(self):
        recheck_name = 'Recheck exact main before preview upload'
        upload_name = 'Deploy preview on existing SWA only'
        self.assertLess(DEV.index('      - name: ' + recheck_name), DEV.index('      - name: ' + upload_name))
        tail = DEV.split('      - name: ' + recheck_name, 1)[1]
        self.assertTrue(tail.split('      - name:', 1)[1].startswith(' ' + upload_name))
        for guard_name in ('Require exact current protected main', recheck_name):
            with self.subTest(guard=guard_name):
                body = step(guard_name)
                self.assertIn('git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main', body)
                source = body.split("run: |\n", 1)[1]
                self._run_exact_main_guard(textwrap.dedent(source))

    def _run_exact_main_guard(self, source):
        with tempfile.TemporaryDirectory() as temp_dir:
            git = Path(temp_dir) / 'git'
            git.write_text('#!/bin/sh\n'
                           'if [ "$1" = "fetch" ]; then exit 0; fi\n'
                           'if [ "$1" = "rev-parse" ]; then printf "%s\\n" "$FAKE_CURRENT_MAIN_SHA"; exit 0; fi\n'
                           'exit 88\n')
            git.chmod(0o755)
            for current, expected_success in ((SHA, True), ('b' * 40, False)):
                with self.subTest(current=current):
                    env = dict(os.environ, PATH=temp_dir + os.pathsep + os.environ['PATH'],
                               SOURCE_SHA=SHA, FAKE_CURRENT_MAIN_SHA=current)
                    outcome = subprocess.run(['bash', '-c', source], env=env,
                                             capture_output=True, text=True, check=False)
                    self.assertEqual(outcome.returncode == 0, expected_success)
                    if not expected_success:
                        self.assertIn('stale ancestor', outcome.stderr)

    def run_identity(self, actual=SHA, origin=ORIGIN, status=200, response_url=None):
        body = step('Verify deployed DEV frontend identity without writes')
        source = re.search(r"python3 - <<'PYCODE'\n(.*?)^          PYCODE", body, re.M | re.S).group(1)
        source = textwrap.dedent(source)
        response = io.StringIO(json.dumps({'build_sha': actual}))
        response.status = status
        response.geturl = lambda: response_url or ORIGIN + '/build.json'
        with patch.dict(os.environ, SOURCE_SHA=SHA, PREVIEW_URL=origin), patch('urllib.request.urlopen', return_value=response) as request, contextlib.redirect_stdout(io.StringIO()):
            exec(compile(source, '<workflow-identity>', 'exec'), {})
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[0], ORIGIN + '/build.json')

    def test_exact_deployed_identity_passes_with_get_only(self):
        self.run_identity()

    def test_stale_deployed_identity_fails(self):
        with self.assertRaisesRegex(SystemExit, 'identity mismatch'):
            self.run_identity(actual='b' * 40)

    def test_non_200_fails(self):
        with self.assertRaisesRegex(SystemExit, 'identity mismatch'):
            self.run_identity(status=404)

    def test_redirected_build_identity_fails_even_when_sha_matches(self):
        for url in (ORIGIN + '/other-build.json', 'https://untrusted.invalid/build.json'):
            with self.subTest(url=url), self.assertRaisesRegex(SystemExit, 'redirected'):
                self.run_identity(response_url=url)

    def test_unowned_or_production_origin_fails_before_request(self):
        for origin in ('https://attacker.invalid', ORIGIN + '.attacker.invalid', 'https://yellow-forest-0eecc8b0f.7.azurestaticapps.net'):
            with self.subTest(origin=origin), self.assertRaisesRegex(SystemExit, 'Unexpected DEV preview origin'):
                self.run_identity(origin=origin)


if __name__ == '__main__':
    unittest.main()
