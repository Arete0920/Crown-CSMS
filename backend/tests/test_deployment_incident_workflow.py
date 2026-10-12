"""Execute recovery decisions and workflow scripts without Azure or GitHub mutations."""
import json
from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/prod-rollback-on-failure.yml'


class DeploymentIncidentWorkflowTests(unittest.TestCase):
    def test_decision_matrix(self):
        result = subprocess.run(['node', '--test', 'scripts/ops/test_deployment_incident.cjs'],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_actual_workflow_classifies_exact_attempt_before_azure(self):
        steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['rollback']['steps']
        names = [step['name'] for step in steps]
        classify = next(step for step in steps if step.get('id') == 'upstream_evidence')
        self.assertLess(names.index(classify['name']), names.index('Recheck live health before rollback'))
        self.assertLess(names.index('Recheck live health before rollback'), names.index('Azure Login'))
        for name in ['Azure Login', 'Resolve last-known-good immutable deploy SHA',
                     'Restore immutable last-known-good image', 'Verify restored runtime identity and health']:
            step = steps[names.index(name)]
            self.assertEqual(step['if'], "${{ steps.health_recheck.outputs.rollback_needed == 'true' }}")
        script = classify['with']['script']
        wrapper = '''const assert = require('node:assert/strict');
const outputs = {};
const core = {setOutput: (key, value) => outputs[key] = value};
const context = {repo: {owner: 'owner', repo: 'repo'}, payload: {workflow_run: {id: 42, run_attempt: 3}}};
const marker = {};
const github = {rest: {actions: {listJobsForWorkflowRunAttempt: marker}},
  paginate: async (method, args) => {
    assert.equal(method, marker); assert.equal(args.run_id, 42); assert.equal(args.attempt_number, 3);
    return ['production-migration', 'build-and-deploy'].map(name =>
      ({name, status: 'completed', conclusion: 'skipped', steps: null}));
  }};
(async () => { SCRIPT
assert.equal(outputs.production_mutation, 'no'); })().catch(error => {console.error(error); process.exit(1)});
'''.replace('SCRIPT', script)
        result = subprocess.run(['node', '-e', wrapper], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_actual_health_script_cannot_authorize_preflight_rollback(self):
        import os
        import tempfile
        steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['rollback']['steps']
        step = next(step for step in steps if step.get('id') == 'health_recheck')
        for mutation, expected in [('no', 'false'), ('unknown', 'unknown'), ('possible', 'true')]:
            with tempfile.NamedTemporaryFile() as output:
                env = dict(os.environ, GITHUB_OUTPUT=output.name, WEBAPP_NAME='test',
                           PRODUCTION_MUTATION=mutation)
                # curl is mocked: no network and no Azure changes; failed network remains unknown.
                script = 'curl() { return 1; }; export -f curl;\n' + step['run']
                result = subprocess.run(['bash', '-c', script], cwd=ROOT, env=env,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                output.seek(0)
                rows = dict(line.split('=', 1) for line in output.read().decode().splitlines())
                self.assertEqual(rows['rollback_needed'], expected)
                self.assertEqual(rows['health_status'], 'unknown')

    def test_actual_issue_script_handles_missing_login_evidence(self):
        steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['rollback']['steps']
        step = next(step for step in steps if step['name'] == 'Open incident or advisory issue')
        wrapper = '''const assert = require('node:assert/strict');
const process = {env: {}};
const context = {repo: {owner: 'owner', repo: 'repo'}, payload: {workflow_run: {}}};
const github = {rest: {issues: {create: async row => {
  assert.match(row.title, /status unknown/); assert.ok(!row.labels.includes('rollback-failed'));
  assert.match(row.body, /Rollback required: unknown/);
}}}};
(async () => { SCRIPT })().catch(error => {console.error(error); global.process.exit(1)});
'''.replace('SCRIPT', step['with']['script'])
        result = subprocess.run(['node', '-e', wrapper], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
