from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "execution" / "999_finish_right_4h_gauntlet.ps1"
DIAGNOSTICS_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_repository_diagnostics.psm1"
BACKEND_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_backend_validation.psm1"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "p0-go-readiness.yml"


def test_repository_diagnostics_are_extracted_without_changing_step_contracts():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = DIAGNOSTICS_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $repositoryDiagnosticsModule -Force" in wrapper
    assert 'Invoke-InfoStep -Name "01_repo_truth"' in wrapper
    assert 'Invoke-InfoStep -Name "02_blocker_signal_scan"' in wrapper
    assert "Invoke-GauntletRepositoryTruth" in wrapper
    assert "Invoke-GauntletBlockerSignalScan" in wrapper

    assert "git branch --show-current" in module
    assert "git rev-parse HEAD" in module
    assert "git status --short --branch" in module
    assert "git log --oneline -n 20" in module
    assert "git grep -n -E" in module


def test_backend_validation_is_extracted_with_equivalent_required_steps():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = BACKEND_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $backendValidationModule -Force" in wrapper
    assert "Get-GauntletBackendValidationSteps" in wrapper
    assert "foreach ($step in $backendValidationSteps)" in wrapper

    expected_names = (
        "03_backend_django_check",
        "04_backend_migration_dry_run",
        "05_backend_core_smoke",
        "06_backend_security_contracts",
    )
    for name in expected_names:
        assert name in module
        assert name not in wrapper

    for command in (
        'Args = @("manage.py", "check")',
        'Args = @("manage.py", "makemigrations", "--check", "--dry-run")',
        '"backend/core/tests/test_permission_engine.py"',
        '"backend/tests/test_tenant_isolation.py"',
        '"backend/crown_api/tests/test_health.py"',
        '"backend/crown_api/tests/test_dashboard_snapshot_summary_api.py"',
        '"backend/tests/test_release_security_permission_contracts.py"',
        '"backend/tests/test_release_security_readiness_contracts.py"',
    ):
        assert command in module

    assert module.count('Required = "YES"') == 4


def test_gauntlet_remains_fail_closed_and_preserves_evidence_schema():
    wrapper = WRAPPER.read_text(encoding="utf-8")

    for field in ("Step", "ExitCode", "Log", "Required", "Passed"):
        assert field in wrapper
    assert '$resultsPath = Join-Path $base "00_results.csv"' in wrapper
    assert '$summaryPath = Join-Path $base "00_SUMMARY.md"' in wrapper
    assert '$_.Required -eq "YES" -and -not $_.Passed' in wrapper
    assert "if ($requiredFailures.Count -gt 0)" in wrapper
    assert "exit 1" in wrapper


def test_workflow_still_invokes_legacy_wrapper_with_exact_sha_evidence():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "999_finish_right_4h_gauntlet.ps1" in workflow
    assert "expected_sha" in workflow
    assert "audit-artifacts/finish-right-4h-*" in workflow
    assert "if: always()" in workflow
