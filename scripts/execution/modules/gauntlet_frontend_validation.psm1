Set-StrictMode -Version Latest

function Get-GauntletFrontendValidationSteps {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$FrontendRoot,

        [Parameter(Mandatory = $true)]
        [string]$NpmExe
    )

    return @(
        [pscustomobject]@{ Name = "07_frontend_npm_ci"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("ci"); Required = "YES" },
        [pscustomobject]@{ Name = "08_frontend_lint"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "lint"); Required = "YES" },
        [pscustomobject]@{ Name = "09_frontend_contracts"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "test:contracts"); Required = "YES" },
        [pscustomobject]@{ Name = "10_frontend_shell_certification"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "check:shell-certification"); Required = "YES" },
        [pscustomobject]@{ Name = "11_frontend_shell_backend_contract_parity"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "check:shell-backend-contract-parity"); Required = "YES" },
        [pscustomobject]@{ Name = "12_frontend_dashboard_completeness"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "verify:dashboard-completeness"); Required = "YES" },
        [pscustomobject]@{ Name = "13_frontend_build"; WorkingDirectory = $FrontendRoot; Exe = $NpmExe; Args = @("run", "build"); Required = "YES" }
    )
}

Export-ModuleMember -Function Get-GauntletFrontendValidationSteps
