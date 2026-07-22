import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_SUMMARY_MODULE = (
    REPO_ROOT
    / "scripts"
    / "execution"
    / "modules"
    / "gauntlet_evidence_summary.psm1"
)


def _powershell_command() -> str:
    command = shutil.which("pwsh") or shutil.which("powershell")
    if command is None:
        pytest.skip("PowerShell is required for the gauntlet evidence-summary contract.")
    return command


def _invoke_summary(tmp_path: Path, *, required_failure: bool) -> dict:
    evidence_root = tmp_path / ("fail" if required_failure else "pass")
    evidence_root.mkdir()
    exit_code = 1 if required_failure else 0
    passed = "$false" if required_failure else "$true"
    module_path = str(EVIDENCE_SUMMARY_MODULE).replace("'", "''")
    evidence_path = str(evidence_root).replace("'", "''")
    repo_path = str(REPO_ROOT).replace("'", "''")

    script = f"""
$ErrorActionPreference = 'Stop'
Import-Module '{module_path}' -Force
$results = @(
    [pscustomobject]@{{
        Step = 'contract_step'
        ExitCode = {exit_code}
        Log = 'contract.log'
        Required = 'YES'
        Passed = {passed}
    }}
)
$output = @(Write-GauntletEvidenceSummary -Results $results -EvidenceRoot '{evidence_path}' -RepoRoot '{repo_path}')
[pscustomobject]@{{
    OutputCount = $output.Count
    TypeName = $output[0].GetType().FullName
    ResultsPath = $output[0].ResultsPath
    SummaryPath = $output[0].SummaryPath
    RequiredFailureCount = @($output[0].RequiredFailures).Count
}} | ConvertTo-Json -Compress
"""

    completed = subprocess.run(
        [_powershell_command(), "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = completed.stdout.strip().splitlines()[-1]
    return json.loads(payload)


@pytest.mark.parametrize(
    ("required_failure", "expected_failure_count"),
    ((False, 0), (True, 1)),
)
def test_summary_function_emits_exactly_one_contract_object(
    tmp_path: Path,
    required_failure: bool,
    expected_failure_count: int,
):
    result = _invoke_summary(tmp_path, required_failure=required_failure)

    assert result["OutputCount"] == 1
    assert result["TypeName"] == "System.Management.Automation.PSCustomObject"
    assert Path(result["ResultsPath"]).name == "00_results.csv"
    assert Path(result["SummaryPath"]).name == "00_SUMMARY.md"
    assert result["RequiredFailureCount"] == expected_failure_count
