Set-StrictMode -Version Latest

function Get-GauntletReleaseContractValidationSteps {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    return @(
        [pscustomobject]@{
            Name = "14_release_api_contracts"
            WorkingDirectory = $RepoRoot
            Exe = "node"
            Args = @("scripts/release/verify-api-contracts.mjs")
            Required = "YES"
        },
        [pscustomobject]@{
            Name = "15_release_navigation_surface"
            WorkingDirectory = $RepoRoot
            Exe = "node"
            Args = @("scripts/release/verify-navigation-surface.mjs")
            Required = "YES"
        }
    )
}

Export-ModuleMember -Function Get-GauntletReleaseContractValidationSteps
