from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "execution" / "999_finish_right_4h_gauntlet.ps1"
DIAGNOSTICS_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_repository_diagnostics.psm1"
BACKEND_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_backend_validation.psm1"
FRONTEND_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_frontend_validation.psm1"
RELEASE_CONTRACT_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_release_contract_validation.psm1"
DEEP_ORCHESTRATION_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_deep_orchestration.psm1"
STATIC_ASSERTIONS_MODULE = REPO_ROOT / "scripts" / "execution" / "modules" / "gauntlet_static_assertions.psm1"
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


def test_frontend_validation_is_extracted_with_equivalent_required_steps():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = FRONTEND_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $frontendValidationModule -Force" in wrapper
    assert "Get-GauntletFrontendValidationSteps" in wrapper
    assert "foreach ($step in $frontendValidationSteps)" in wrapper

    expected = {
        "07_frontend_npm_ci": '("ci")',
        "08_frontend_lint": '("run", "lint")',
        "09_frontend_contracts": '("run", "test:contracts")',
        "10_frontend_shell_certification": '("run", "check:shell-certification")',
        "11_frontend_shell_backend_contract_parity": '("run", "check:shell-backend-contract-parity")',
        "12_frontend_dashboard_completeness": '("run", "verify:dashboard-completeness")',
        "13_frontend_build": '("run", "build")',
    }
    for name, args in expected.items():
        assert name in module
        assert args in module
        assert name not in wrapper

    assert module.count('Required = "YES"') == 7
    assert "WorkingDirectory = $FrontendRoot" in module
    assert "Exe = $NpmExe" in module


def test_release_contract_validation_is_extracted_with_equivalent_required_steps():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = RELEASE_CONTRACT_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $releaseContractValidationModule -Force" in wrapper
    assert "Get-GauntletReleaseContractValidationSteps" in wrapper
    assert "foreach ($step in $releaseContractValidationSteps)" in wrapper

    expected = {
        "14_release_api_contracts": "scripts/release/verify-api-contracts.mjs",
        "15_release_navigation_surface": "scripts/release/verify-navigation-surface.mjs",
    }
    for name, script in expected.items():
        assert name in module
        assert script in module
        assert name not in wrapper

    assert module.count('Required = "YES"') == 2
    assert "WorkingDirectory = $RepoRoot" in module
    assert 'Exe = "node"' in module


def test_deep_orchestration_is_extracted_with_equivalent_required_steps():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = DEEP_ORCHESTRATION_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $deepOrchestrationModule -Force" in wrapper
    assert "Get-GauntletDeepOrchestrationSteps" in wrapper
    assert "foreach ($step in $deepOrchestrationSteps)" in wrapper

    expected = {
        "16_dashboard_completion_gate_deep": "./scripts/execution/105_dashboard_module_completion_gate.ps1",
        "17_full_completion_truth_gate_deep": "./scripts/execution/106_crown_full_completion_truth_gate.ps1",
    }
    for name, script in expected.items():
        assert name in module
        assert script in module
        assert name not in wrapper

    assert module.count('Required = "YES"') == 2
    assert module.count('"-Deep"') == 2
    assert module.count('"-ExecutionPolicy", "Bypass", "-File"') == 2
    assert "WorkingDirectory = $RepoRoot" in module
    assert "Exe = $PowerShellExe" in module


def test_static_assertions_are_extracted_with_equivalent_required_definitions():
    wrapper = WRAPPER.read_text(encoding="utf-8")
    module = STATIC_ASSERTIONS_MODULE.read_text(encoding="utf-8")

    assert "Import-Module $staticAssertionsModule -Force" in wrapper
    assert "Get-GauntletStaticAssertions" in wrapper
    assert "foreach ($assertion in $staticAssertions)" in wrapper
    assert "Invoke-StaticAssertion -Name $assertion.Name -Path $assertion.Path -Patterns $assertion.Patterns" in wrapper

    expected = {
        "18_sandbox_nav_flag_static_assertions": (
            "frontend/dashboards/src/components/navigation/dashboardNavConfig.js",
            (
                "VITE_SANDBOX_READY_ONLY",
                "VITE_HIDE_UNREADY_NAV",
                "VITE_SANDBOX_MODE",
                "isProductionReady",
                "visibleStaticSections = readyOnly",
            ),
        ),
        "19_backend_dashboard_sample_fail_closed_assertions": (
            "backend/crown_api/dashboards/views.py",
            (
                "CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS",
                "dashboard_live_data_required",
                "No live or snapshot payload is available",
                "sample_payload_allowed",
            ),
        ),
    }
    for name, (path, patterns) in expected.items():
        assert name in module
        assert path in module
        assert name not in wrapper
        for pattern in patterns:
            assert pattern in module
            assert pattern not in wrapper


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
