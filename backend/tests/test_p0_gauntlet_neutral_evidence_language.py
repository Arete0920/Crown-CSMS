from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_MODULE = (
    REPO_ROOT
    / "scripts"
    / "execution"
    / "modules"
    / "gauntlet_evidence_summary.psm1"
)
WRAPPER = REPO_ROOT / "scripts" / "execution" / "999_finish_right_4h_gauntlet.ps1"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "p0-go-readiness.yml"


def test_summary_uses_neutral_technical_evidence_language():
    module = SUMMARY_MODULE.read_text(encoding="utf-8")

    assert "# P0 Technical Evidence Summary" in module
    assert "## Technical evidence result" in module
    assert "SATISFIED" in module
    assert "UNSATISFIED" in module
    assert "Release authority: not determined by this workflow" in module
    assert "This is not production authorization" in module

    assert "# Finish Right 4H Gauntlet Summary" not in module
    assert 'Add("## Verdict")' not in module
    assert 'Add("PASS")' not in module
    assert 'Add("FAIL")' not in module
    assert "production approved" not in module.lower()
    assert "production ready" not in module.lower()


def test_neutral_language_change_preserves_fail_closed_execution_contract():
    module = SUMMARY_MODULE.read_text(encoding="utf-8")
    wrapper = WRAPPER.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert '$_.Required -eq "YES" -and -not $_.Passed' in module
    assert "RequiredFailures = $requiredFailures" in module
    assert "if ($requiredFailures.Count -gt 0)" in wrapper
    assert "exit 1" in wrapper
    assert "999_finish_right_4h_gauntlet.ps1" in workflow
    assert "expected_sha" in workflow
    assert "if: always()" in workflow
