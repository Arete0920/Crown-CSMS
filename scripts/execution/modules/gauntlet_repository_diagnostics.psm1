Set-StrictMode -Version Latest

function Invoke-GauntletRepositoryTruth {
    [CmdletBinding()]
    param()

    git branch --show-current
    git rev-parse HEAD
    git status --short --branch
    git log --oneline -n 20
}

function Invoke-GauntletBlockerSignalScan {
    [CmdletBinding()]
    param()

    git grep -n -E "NO-GO|NOT VERIFIED|NOT DONE|BLOCKER|REVIEW REQUIRED|placeholder|sample data|not implemented|coming soon|TODO|FIXME" -- docs scripts backend frontend .github
}

Export-ModuleMember -Function Invoke-GauntletRepositoryTruth, Invoke-GauntletBlockerSignalScan
