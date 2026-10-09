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

    def test_each_mandatory_dependency_is_enforced_in_both_entrypoints(self):
        required = {
            'candidate-verification': {'resolve-release'},
            'production-migration': {'resolve-release', 'candidate-verification'},
            'build-and-deploy': {'resolve-release', 'candidate-verification', 'production-migration'},
        }
        for filename in policy.WORKFLOWS:
            original = yaml.safe_load((ROOT / '.github/workflows' / filename).read_text())
            for job_name, dependencies in required.items():
                for dependency in dependencies:
                    with self.subTest(workflow=filename, job=job_name, missing=dependency):
                        workflow = copy.deepcopy(original)
                        job = workflow['jobs'][job_name]
                        job['needs'] = sorted(policy.needs(job) - {dependency})
                        errors = policy.validate(workflow)
                        self.assertIn(
                            f'{job_name} missing mandatory prerequisites: {dependency}', errors)

    def test_job_bypasses_are_rejected_in_both_entrypoints(self):
        for filename in policy.WORKFLOWS:
            original = yaml.safe_load((ROOT / '.github/workflows' / filename).read_text())
            for job_name in ('candidate-verification', 'production-migration', 'build-and-deploy'):
                for field, value in [('if', '${{ always() }}'),
                                     ('if', '${{ !cancelled() }}'), ('if', False),
                                     ('continue-on-error', True),
                                     ('continue-on-error', '${{ true }}')]:
                    with self.subTest(workflow=filename, job=job_name, field=field, value=value):
                        workflow = copy.deepcopy(original)
                        workflow['jobs'][job_name][field] = value
                        errors = policy.validate(workflow)
                        expected = (f'{job_name} job must fail closed' if field == 'continue-on-error'
                                    else f'{job_name} job cannot bypass default successful dependency semantics')
                        self.assertIn(expected, errors)

    def test_missing_release_resolution_job_is_rejected(self):
        del self.workflow['jobs']['resolve-release']
        self.assertIn('missing release resolution job', policy.validate(self.workflow))

    def test_dependency_order_and_additional_prerequisites_are_allowed(self):
        for filename in policy.WORKFLOWS:
            workflow = yaml.safe_load((ROOT / '.github/workflows' / filename).read_text())
            workflow['jobs']['additional-security-gate'] = {
                'runs-on': 'ubuntu-latest', 'steps': [{'run': 'true'}]}
            for name in ('production-migration', 'build-and-deploy'):
                workflow['jobs'][name]['needs'].reverse()
                workflow['jobs'][name]['needs'].append('additional-security-gate')
            self.assertEqual(policy.validate(workflow), [], filename)

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
