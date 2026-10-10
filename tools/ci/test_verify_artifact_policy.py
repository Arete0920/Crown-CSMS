import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('artifact_policy', Path(__file__).with_name('verify_artifact_policy.py'))
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class ArtifactPolicyTests(unittest.TestCase):
    def workflow(self, **options):
        return {'jobs': {'proof': {'steps': [{'uses': 'actions/upload-artifact@' + 'a' * 40,
                'with': {'path': 'report.json', 'retention-days': 14, 'if-no-files-found': 'error', **options}}]}}}

    def test_mandatory_evidence_with_bounded_retention_passes(self):
        self.assertEqual(policy.violations(self.workflow()), [])

    def test_missing_retention_is_rejected(self):
        self.assertTrue(policy.violations(self.workflow(**{'retention-days': None})))

    def test_excessive_or_dynamic_retention_is_rejected(self):
        for value in (0, 365, '${{ inputs.days }}', True):
            self.assertTrue(policy.violations(self.workflow(**{'retention-days': value})))

    def test_missing_file_behavior_must_be_explicit(self):
        self.assertTrue(policy.violations(self.workflow(**{'if-no-files-found': None})))

    def test_whole_worktree_and_historical_evidence_globs_are_rejected(self):
        for path in ('.', '**/*', 'audit-artifacts/**', 'docs/release/**'):
            self.assertTrue(policy.violations(self.workflow(path=path)))

    def test_optional_diagnostic_policy_is_explicit(self):
        self.assertEqual(policy.violations(self.workflow(**{'if-no-files-found': 'ignore'})), [])


if __name__ == '__main__':
    unittest.main()
