Set-StrictMode -Version Latest

function Write-GauntletEvidenceSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IEnumerable]$Results,

        [Parameter(Mandatory = $true)]
        [string]$EvidenceRoot,

        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $resultsPath = Join-Path $EvidenceRoot "00_results.csv"
    $Results | Export-Csv -Path $resultsPath -NoTypeInformation -Encoding UTF8

    $requiredFailures = @($Results | Where-Object { $_.Required -eq "YES" -and -not $_.Passed })
    $summaryPath = Join-Path $EvidenceRoot "00_SUMMARY.md"
    $lines = New-Object System.Collections.Generic.List[string]
    [void]$lines.Add("# P0 Technical Evidence Summary")
    [void]$lines.Add("")
    [void]$lines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    [void]$lines.Add("- Repo root: $RepoRoot")
    [void]$lines.Add("- Evidence root: $EvidenceRoot")
    [void]$lines.Add("- Required technical failures: $($requiredFailures.Count)")
    [void]$lines.Add("- Release authority: not determined by this workflow")
    [void]$lines.Add("")
    [void]$lines.Add("## Technical evidence result")
    [void]$lines.Add("")
    if ($requiredFailures.Count -eq 0) {
        [void]$lines.Add("SATISFIED")
        [void]$lines.Add("")
        [void]$lines.Add("All required technical steps completed successfully for this execution identity. This is not production authorization.")
    }
    else {
        [void]$lines.Add("UNSATISFIED")
        [void]$lines.Add("")
        [void]$lines.Add("One or more required technical steps failed. Production authorization is not implied in either outcome.")
        [void]$lines.Add("")
        [void]$lines.Add("## Required technical failures")
        [void]$lines.Add("")
        foreach ($failure in $requiredFailures) {
            [void]$lines.Add("- $($failure.Step) exit=$($failure.ExitCode) log=$($failure.Log)")
        }
    }
    $lines | Set-Content -Path $summaryPath -Encoding UTF8

    return [pscustomobject]@{
        ResultsPath = $resultsPath
        SummaryPath = $summaryPath
        RequiredFailures = $requiredFailures
    }
}

Export-ModuleMember -Function Write-GauntletEvidenceSummary
