"""Mutation proofs: incomplete or bypassed validation never authorizes production."""
import copy
import importlib.util
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('candidate_order', ROOT / 'tools/verify_release_candidate_order.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class CandidateOrderTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load((ROOT / '.github/workflows/deploy-prod.yml').read_text())

    def test_both_release_entrypoints_satisfy_contract(self):
        for name in policy.WORKFLOWS:
            workflow = yaml.safe_load((ROOT / '.github/workflows' / name).read_text())
            self.assertEqual(policy.validate(workflow), [], name)

    def test_migration_without_validation_is_rejected(self):
        self.workflow['jobs']['production-migration']['needs'] = 'resolve-release'
        self.assertTrue(policy.validate(self.workflow))

    def test_always_migration_cannot_bypass_failed_candidate(self):
        self.workflow['jobs']['production-migration']['if'] = '${{ always() }}'
        self.assertTrue(policy.validate(self.workflow))

    def test_skipped_or_nonblocking_scan_is_rejected(self):
        for field, value in [('if', 'false'), ('continue-on-error', True)]:
            workflow = copy.deepcopy(self.workflow)
            scan = next(s for s in workflow['jobs']['candidate-verification']['steps']
                        if s.get('name') == 'Run blocking security scan (Trivy)')
            scan[field] = value
            self.assertTrue(policy.validate(workflow))

    def test_advisory_scan_is_rejected(self):
        scan = next(s for s in self.workflow['jobs']['candidate-verification']['steps']
                    if s.get('name') == 'Run blocking security scan (Trivy)')
        scan['with']['exit-code'] = '0'
        self.assertTrue(policy.validate(self.workflow))

    def test_publish_before_scan_is_rejected(self):
        steps = self.workflow['jobs']['candidate-verification']['steps']
        publish = next(s for s in steps if s.get('name') == 'Publish validated candidate and record digest')
        steps.remove(publish)
        steps.insert(0, publish)
        self.assertTrue(policy.validate(self.workflow))

    def test_mutable_deploy_tag_is_rejected(self):
        deploy = next(s for s in self.workflow['jobs']['build-and-deploy']['steps']
                      if 'azure/webapps-deploy' in s.get('uses', ''))
        deploy['with']['images'] = 'registry/image:latest'
        self.assertTrue(policy.validate(self.workflow))

    def test_rebuilding_validated_image_is_rejected(self):
        self.workflow['jobs']['build-and-deploy']['steps'].append({'uses': 'docker/build-push-action@abc'})
        self.assertTrue(policy.validate(self.workflow))


if __name__ == '__main__':
    unittest.main()
