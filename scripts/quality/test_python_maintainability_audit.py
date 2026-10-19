"""Tests for the dependency-free Python maintainability inventory."""

import json
from pathlib import Path

import pytest

from python_maintainability_audit import main, scan_root, scan_text


def test_reports_missing_annotations_docstrings_and_reviewable_loops() -> None:
    """Find actual omissions without rewriting a function or its loop."""
    source = (
        "def build(items):\n"
        "    result = []\n"
        "    for item in items:\n"
        "        result.append(item * 2)\n"
        "    return result\n"
    )
    findings = scan_text("example.py", source)
    assert {(item.line, item.rule) for item in findings} == {
        (1, "missing_docstring"),
        (1, "missing_return_type"),
        (1, "missing_parameter_types"),
        (3, "append_loop_review"),
    }


def test_typed_documented_async_method_has_no_false_positives() -> None:
    """Recognize documented typed methods and skip implicit self typing."""
    source = (
        "class Reader:\n"
        "    async def read(self, page: int) -> str:\n"
        '        """Read a single page."""\n'
        "        return str(page)\n"
    )
    assert scan_text("reader.py", source) == []


def test_reports_bounded_location_without_code_excerpt() -> None:
    """Avoid placing source contents in inventory findings."""
    source = "secret = '" + ("x" * 80) + "'\n"
    findings = scan_text("sample.py", source)
    assert len(findings) == 1
    assert findings[0].rule == "line_over_79"
    assert "xxx" not in repr(findings[0])


def test_skips_generated_directories_and_sorts_paths(tmp_path: Path) -> None:
    """Inspect application files but exclude migrations and archive copies."""
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "z.py").write_text("def z():\n    pass\n")
    (tmp_path / "backend" / "a.py").write_text("def a():\n    pass\n")
    for name in ("migrations", "archive", ".venv"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "ignored.py").write_text("def ignored(): pass")
    report = scan_root(tmp_path)
    assert report.scanned_files == 2
    assert report.skipped_files == 0
    assert [item.path for item in report.findings][:2] == [
        "backend/a.py",
        "backend/a.py",
    ]


def test_syntax_errors_are_reported_without_execution() -> None:
    """Report unparseable Python rather than importing broken modules."""
    findings = scan_text("broken.py", "def broken(:\n    pass\n")
    assert any(item.rule == "syntax_error" for item in findings)


def test_json_output_limits_locations_but_preserves_totals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Keep full counts even when only one finding is displayed."""
    (tmp_path / "test.py").write_text("def bad(x):\n    return x\n")
    assert main([str(tmp_path), "--format", "json", "--limit", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["scanned_files"] == 1
    assert result["total_findings"] == 3
    assert len(result["findings"]) == 1


def test_invalid_root_and_limits_rejected(tmp_path: Path) -> None:
    """Fail clearly for invalid roots, byte limits, and output limits."""
    with pytest.raises(ValueError, match="existing directory"):
        scan_root(tmp_path / "missing")
    with pytest.raises(ValueError, match="positive"):
        scan_root(tmp_path, max_file_bytes=0)
    with pytest.raises(ValueError, match="negative"):
        main([str(tmp_path), "--limit", "-1"])
def test_symlinked_file_is_not_read(tmp_path: Path) -> None:
    """Never follow checkout symlinks into an external private source file."""
    outside = tmp_path.parent / "outside-audit-target.py"
    outside.write_text("def outside(secret):\n    return secret\n")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("file symlink creation unavailable on this platform")
    try:
        report = scan_root(tmp_path)
        assert report.scanned_files == 0
        assert report.skipped_files == 1
        assert report.findings == ()
    finally:
        outside.unlink()
