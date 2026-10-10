"""Require bounded artifact retention and explicit missing-evidence behavior."""
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]


def violations(workflow):
    errors = []
    for job_name, job in workflow.get('jobs', {}).items():
        for step in job.get('steps', []):
            if 'actions/upload-artifact@' not in step.get('uses', ''):
                continue
            options = step.get('with', {})
            name = f"{job_name}/{step.get('name', 'upload')}"
            retention = options.get('retention-days')
            if type(retention) is not int or not 1 <= retention <= 30:
                errors.append(f'{name}: explicit retention from 1 to 30 days is required')
            if options.get('if-no-files-found') not in {'error', 'warn', 'ignore'}:
                errors.append(f'{name}: explicit missing-file policy is required')
            paths = str(options.get('path', '')).splitlines()
            if any(p.strip() in {'.', './', '**', '**/*', 'audit-artifacts/**', 'docs/release/**'} for p in paths):
                errors.append(f'{name}: entire worktree or broad historical evidence upload is forbidden')
    return errors


def main():
    errors = []
    for path in sorted((ROOT / '.github/workflows').glob('*.y*ml')):
        try:
            workflow = yaml.safe_load(path.read_text())
            errors.extend(f'{path.name}: {e}' for e in violations(workflow))
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(f'{path.name}: {exc}')
    if errors:
        print('\n'.join(errors))
        return 1
    print('PASS: bounded retention and explicit missing-evidence policy for all artifact uploads')
    return 0


if __name__ == '__main__':
    sys.exit(main())
