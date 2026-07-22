Set-StrictMode -Version Latest

function Get-GauntletBackendValidationSteps {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        [Parameter(Mandatory = $true)]
        [string]$PythonExe
    )

    $backendSmokeArgs = @(
        "-m", "pytest",
        "backend/core/tests/test_permission_engine.py",
        "backend/tests/test_tenant_isolation.py",
        "backend/crown_api/tests/test_health.py",
        "backend/crown_api/tests/test_dashboard_snapshot_summary_api.py",
        "-q", "--nomigrations"
    )

    $backendSecurityArgs = @(
        "-m", "pytest",
        "backend/tests/test_release_security_permission_contracts.py",
        "backend/tests/test_release_security_readiness_contracts.py",
        "-q", "--nomigrations"
    )

    return @(
        [pscustomobject]@{
            Name = "03_backend_django_check"
            WorkingDirectory = $RepoRoot
            Exe = $PythonExe
            Args = @("manage.py", "check")
            Required = "YES"
        },
        [pscustomobject]@{
            Name = "04_backend_migration_dry_run"
            WorkingDirectory = $RepoRoot
            Exe = $PythonExe
            Args = @("manage.py", "makemigrations", "--check", "--dry-run")
            Required = "YES"
        },
        [pscustomobject]@{
            Name = "05_backend_core_smoke"
            WorkingDirectory = $RepoRoot
            Exe = $PythonExe
            Args = $backendSmokeArgs
            Required = "YES"
        },
        [pscustomobject]@{
            Name = "06_backend_security_contracts"
            WorkingDirectory = $RepoRoot
            Exe = $PythonExe
            Args = $backendSecurityArgs
            Required = "YES"
        }
    )
}

Export-ModuleMember -Function Get-GauntletBackendValidationSteps
