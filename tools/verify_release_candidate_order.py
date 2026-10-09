"""Reject deployment graphs that mutate production before candidate validation."""
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ('deploy-prod.yml', 'deploy-prod-dispatch.yml')


def needs(job):
    value = job.get('needs', [])
    return {value} if isinstance(value, str) else set(value)


def validate(workflow):
    errors = []
    jobs = workflow.get('jobs', {})
    candidate = jobs.get('candidate-verification', {})
    deployment = jobs.get('build-and-deploy', {})
    prerequisites = {
        'candidate-verification': {'resolve-release'},
        'production-migration': {'resolve-release', 'candidate-verification'},
        'build-and-deploy': {'resolve-release', 'candidate-verification', 'production-migration'},
    }
    if not jobs.get('resolve-release'):
        errors.append('missing release resolution job')
    for name, required in prerequisites.items():
        job = jobs.get(name, {})
        if not job:
            errors.append(f'missing {name} job')
        missing = required - needs(job)
        if missing:
            errors.append(f'{name} missing mandatory prerequisites: {", ".join(sorted(missing))}')
        if 'if' in job:
            errors.append(f'{name} job cannot bypass default successful dependency semantics')
        if job.get('continue-on-error', False) is not False:
            errors.append(f'{name} job must fail closed')
    steps = candidate.get('steps', [])
    named = {s.get('name'): index for index, s in enumerate(steps)}
    required = ['Run complete governed candidate coverage', 'Verify complete candidate frontend',
                'Build production image for verification', 'Run blocking security scan (Trivy)',
                'Publish validated candidate and record digest']
    if any(name not in named for name in required):
        errors.append('complete candidate test, build, scan and publish chain is required')
    elif [named[n] for n in required] != sorted(named[n] for n in required):
        errors.append('candidate must pass full tests and image scan before publication')
    for s in steps:
        if s.get('name') in required and ('if' in s or s.get('continue-on-error')):
            errors.append('candidate authority steps must execute and fail closed')
    scan = next((s for s in steps if s.get('name') == required[3]), {})
    options = scan.get('with', {})
    if str(options.get('exit-code')) != '1' or options.get('severity') != 'HIGH,CRITICAL':
        errors.append('image vulnerability scan must block high and critical findings')
    build = next((s for s in steps if s.get('name') == required[2]), {})
    if build.get('with', {}).get('push') is not False or build.get('with', {}).get('load') is not True:
        errors.append('image must be built locally and scanned before registry publication')
    outputs = candidate.get('outputs', {})
    if outputs.get('image_digest') != '${{ steps.publish.outputs.image_digest }}':
        errors.append('candidate must expose its validated registry digest')
    deploy_steps = deployment.get('steps', [])
    image = '${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.candidate-verification.outputs.image_digest }}'
    if not any(s.get('with', {}).get('images') == image for s in deploy_steps):
        errors.append('deployment must consume the validated candidate digest')
    for s in deploy_steps:
        if 'docker/build-push-action' in s.get('uses', '') or 'docker build ' in s.get('run', ''):
            errors.append('deployment must not rebuild the validated candidate')
    coverage = next((s for s in steps if s.get('name') == required[0]), {})
    if '-CoverageVersion 7.16.2' not in coverage.get('run', ''):
        errors.append('candidate must use the pinned governed complete coverage runner')
    return errors


def main():
    errors = []
    for name in WORKFLOWS:
        try:
            workflow = yaml.safe_load((ROOT / '.github/workflows' / name).read_text())
            errors.extend(f'{name}: {e}' for e in validate(workflow))
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(f'{name}: invalid release workflow: {exc}')
    if errors:
        print('\n'.join(errors))
        return 1
    print('PASS: candidates are validated before production migration and deployed by digest')
    return 0


if __name__ == '__main__':
    sys.exit(main())
