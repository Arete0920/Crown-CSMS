import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('tool_pins', Path(__file__).with_name('verify_ci_tool_pins.py'))
pins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pins)


class ToolPinTests(unittest.TestCase):
    def workflow(self, name):
        return (pins.ROOT / '.github/workflows' / name).read_text()

    def test_missing_or_changed_pin_is_rejected(self):
        for name, required in pins.REQUIRED.items():
            for missing in required:
                with self.subTest(workflow=name, missing=missing):
                    self.assertTrue(pins.violations(name, self.workflow(name).replace(missing, 'unreviewed')))

    def test_comment_cannot_supply_missing_pin(self):
        name = 'dependency-audit.yml'
        text = self.workflow(name).replace('pip-audit==2.10.1', 'pip-audit')
        self.assertTrue(pins.violations(name, text + '\n# pip-audit==2.10.1\n'))

    def test_reviewed_workflows_pass(self):
        for name in pins.REQUIRED:
            self.assertEqual(pins.violations(name, self.workflow(name)), [])


if __name__ == '__main__':
    unittest.main()
