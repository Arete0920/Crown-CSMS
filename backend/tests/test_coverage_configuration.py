from configparser import ConfigParser
from pathlib import Path


def test_module_style_test_files_are_excluded_from_source_coverage() -> None:
    """Coverage must measure application source, not app-level tests.py modules."""

    repository_root = Path(__file__).resolve().parents[2]
    coverage_config = repository_root / ".coveragerc"

    parser = ConfigParser()
    loaded_files = parser.read(coverage_config, encoding="utf-8")

    assert [Path(filename).resolve() for filename in loaded_files] == [
        coverage_config.resolve()
    ]

    omitted_patterns = {
        pattern.strip()
        for pattern in parser.get("run", "omit").splitlines()
        if pattern.strip()
    }

    assert "*/tests.py" in omitted_patterns
