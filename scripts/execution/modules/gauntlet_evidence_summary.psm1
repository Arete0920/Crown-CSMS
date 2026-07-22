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
    $lines.Add("# Finish Right 4H Gauntlet Summary")
    $lines.Add("")
    $lines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $lines.Add("- Repo root: $RepoRoot")
    $lines.Add("- Evidence root: $EvidenceRoot")
    $lines.Add("- Required failures: $($requiredFailures.Count)")
    $lines.Add("")
    if ($requiredFailures.Count -eq 0) {
        $lines.Add("## Verdict")
        $lines.Add("")
        $lines.Add("PASS")
    }
    else {
        $lines.Add("## Verdict")
        $lines.Add("")
        $lines.Add("FAIL")
        $lines.Add("")
        $lines.Add("## Required failures")
        $lines.Add("")
        foreach ($failure in $requiredFailures) {
            $lines.Add("- $($failure.Step) exit=$($failure.ExitCode) log=$($failure.Log)")
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
