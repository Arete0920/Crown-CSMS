Set-StrictMode -Version Latest

function Get-GauntletDeepOrchestrationSteps {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        [Parameter(Mandatory = $true)]
        [string]$PowerShellExe
    )

    return @(
        [pscustomobject]@{
            Name = "16_dashboard_completion_gate_deep"
            WorkingDirectory = $RepoRoot
            Exe = $PowerShellExe
            Args = @("-ExecutionPolicy", "Bypass", "-File", "./scripts/execution/105_dashboard_module_completion_gate.ps1", "-Deep")
            Required = "YES"
        },
        [pscustomobject]@{
            Name = "17_full_completion_truth_gate_deep"
            WorkingDirectory = $RepoRoot
            Exe = $PowerShellExe
            Args = @("-ExecutionPolicy", "Bypass", "-File", "./scripts/execution/106_crown_full_completion_truth_gate.ps1", "-Deep")
            Required = "YES"
        }
    )
}

Export-ModuleMember -Function Get-GauntletDeepOrchestrationSteps
