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
    [void]$lines.Add("# Finish Right 4H Gauntlet Summary")
    [void]$lines.Add("")
    [void]$lines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    [void]$lines.Add("- Repo root: $RepoRoot")
    [void]$lines.Add("- Evidence root: $EvidenceRoot")
    [void]$lines.Add("- Required failures: $($requiredFailures.Count)")
    [void]$lines.Add("")
    if ($requiredFailures.Count -eq 0) {
        [void]$lines.Add("## Verdict")
        [void]$lines.Add("")
        [void]$lines.Add("PASS")
    }
    else {
        [void]$lines.Add("## Verdict")
        [void]$lines.Add("")
        [void]$lines.Add("FAIL")
        [void]$lines.Add("")
        [void]$lines.Add("## Required failures")
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
