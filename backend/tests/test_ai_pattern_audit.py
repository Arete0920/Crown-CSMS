from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "quality" / "ai_pattern_audit.py"
SPEC = importlib.util.spec_from_file_location("ai_pattern_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def test_detects_high_signal_patterns(tmp_path: Path) -> None:
    script = tmp_path / "finish_now.ps1"
    script.write_text(
        "Set-Location C:\\w\\crown\n"
        '$status = "PASS"\n'
        "# ====================\n",
        encoding="utf-8",
    )
    result = AUDIT.run_audit(tmp_path)
    rules = {item.rule for item in result.findings}
    assert result.scanned_files == 1
    assert {"AP-01", "AP-02", "AP-03", "AP-06"}.issubset(rules)
    assert AUDIT.threshold_reached(result, "high") is True


def test_excludes_generated_and_explicit_paths(tmp_path: Path) -> None:
    generated = tmp_path / "node_modules" / "tmp.cmd"
    generated.parent.mkdir(parents=True)
    generated.write_text("Set-Location C:\\w\\ignored\n", encoding="utf-8")
    excluded = tmp_path / "local" / "tmp.cmd"
    excluded.parent.mkdir(parents=True)
    excluded.write_text("Set-Location C:\\w\\ignored\n", encoding="utf-8")
    source = tmp_path / "src" / "runner.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('ok')\n", encoding="utf-8")
    result = AUDIT.run_audit(tmp_path, exclusions=("local",))
    assert result.scanned_files == 1
    assert result.findings == ()


def test_suppression_is_rule_specific() -> None:
    findings = AUDIT.scan_text(
        "scripts/check.ps1",
        "Set-Location C:\\w\\allowed  # ai-audit: allow AP-02\n$status = \"PASS\"\n",
    )
    rules = [item.rule for item in findings]
    assert "AP-02" not in rules
    assert "AP-03" in rules


def test_json_output_is_stable(tmp_path: Path) -> None:
    source = tmp_path / "src" / "service.py"
    source.parent.mkdir(parents=True)
    source.write_text("try:\n    run()\nexcept Exception:\n    pass\n", encoding="utf-8")
    payload = json.loads(AUDIT.render_result(AUDIT.run_audit(tmp_path), "json"))
    assert payload["scanned_files"] == 1
    assert payload["counts_by_rule"]["AP-04"] == 1
    assert payload["findings"][0]["path"] == "src/service.py"


def test_fail_on_none_never_fails(tmp_path: Path) -> None:
    source = tmp_path / "tmp.py"
    source.write_text("# TODO: replace\n", encoding="utf-8")
    result = AUDIT.run_audit(tmp_path)
    assert result.findings
    assert AUDIT.threshold_reached(result, "none") is False
