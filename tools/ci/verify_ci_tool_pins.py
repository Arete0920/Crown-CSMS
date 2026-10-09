"""Guard reviewed versions of the security and policy tools we execute."""
from pathlib import Path
import sys
import re
import yaml

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    'repository-policy.yml': ['pyyaml==6.0.3',
        'https://github.com/rhysd/actionlint/releases/download/v1.7.1/actionlint_1.7.1_linux_amd64.tar.gz',
        'f53c34493657dfea83b657e4b62cc68c25fbc383dff64c8d581613b037aacaa3',
        'sha256sum --check --strict'],
    'dependency-audit.yml': ['pip-audit==2.10.1', 'pip-licenses==5.5.5', 'license-checker@25.0.1'],
    'license-audit.yml': ['pip-licenses==5.5.5', 'license-checker@25.0.1'],
    'sbom-generation.yml': ['cyclonedx-bom==7.5.0', '@cyclonedx/cyclonedx-npm@6.0.1'],
}


def violations(name, text):
    workflow = yaml.safe_load(text)
    commands = []
    for job in workflow.get('jobs', {}).values():
        for step in job.get('steps', []):
            commands.extend(line for line in step.get('run', '').splitlines()
                            if not line.lstrip().startswith('#'))
    commands = '\n'.join(commands)
    errors = [f'{name}: missing reviewed tool pin/checksum: {pin}'
              for pin in REQUIRED[name] if pin not in commands]
    if 'raw.githubusercontent.com/rhysd/actionlint/main/' in commands:
        errors.append(f'{name}: mutable remote actionlint installer is forbidden')
    expected = {'pip-audit': '==2.10.1', 'pip-licenses': '==5.5.5',
                'cyclonedx-bom': '==7.5.0', 'pyyaml': '==6.0.3',
                'license-checker': '@25.0.1', '@cyclonedx/cyclonedx-npm': '@6.0.1'}
    for tool, version in expected.items():
        for match in re.finditer(r'(?<![\w/-])' + re.escape(tool) + r'([^\s]*)', commands):
            suffix = match[1]
            # Plain CLI execution is expected. Package installation tokens must be pinned.
            line = commands[:match.start()].rsplit('\n', 1)[-1]
            if ('pip install' in line or 'npx --yes' in line) and suffix != version:
                errors.append(f'{name}: unreviewed installation token: {tool}{suffix}')
    if name == 'repository-policy.yml':
        check = commands.find('sha256sum --check --strict')
        extract = commands.find('tar -xzf')
        if check < 0 or extract < check:
            errors.append('actionlint checksum verification must precede archive extraction')
    return errors


def main():
    errors = []
    for name in REQUIRED:
        errors.extend(violations(name, (ROOT / '.github/workflows' / name).read_text()))
    if errors:
        print('\n'.join(errors))
        return 1
    print('PASS: reviewed CI scanner pins and checksum-verified actionlint archive')
    return 0


if __name__ == '__main__':
    sys.exit(main())
