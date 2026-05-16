$prNumber = "814"
$interval = 45
$maxDuration = 35 * 60
$startTime = Get-Date

Write-Host "Monitoring PR #$prNumber..."

while (((Get-Date) - $startTime).TotalSeconds -lt $maxDuration) {
    $checksJson = gh pr checks $prNumber --json name,state,link,bucket,workflow | ConvertFrom-Json
    $viewJson = gh pr view $prNumber --json mergeStateStatus,isDraft,reviewDecision,url | ConvertFrom-Json

    $ready = $true
    $blockers = @()

    # Criteria 1, 2, 3: specific successes
    $accVer = $checksJson | Where-Object { $_.name -eq "accounting-verification" }
    if (-not $accVer -or $accVer.state -ne "SUCCESS") { 
        $ready = $false
        $blockers += "accounting-verification is $($accVer.state -join 'MISSING')" 
    }

    $proofCer = $checksJson | Where-Object { $_.name -eq "proof-ceremony" }
    if (-not $proofCer -or $proofCer.state -ne "SUCCESS") { 
        $ready = $false
        $blockers += "proof-ceremony is $($proofCer.state -join 'MISSING')" 
    }

    $codeQl = $checksJson | Where-Object { $_.name -like "*CodeQL*" }
    foreach ($c in $codeQl) {
        if ($c.state -ne "SUCCESS") {
            $ready = $false
            $blockers += "CodeQL check $($c.name) is $($c.state)"
        }
    }

    # Criteria 4: No FAIL/ERROR/CANCELLED/PENDING except SKIPPED
    foreach ($check in $checksJson) {
        if ($check.state -in @("FAILURE", "ERROR", "CANCELLED", "PENDING") -and $check.state -ne "SKIPPED") {
            $ready = $false
            $blockers += "Check $($check.name) is $($check.state)"
        }
    }

    # Criteria 5: Merge state
    if ($viewJson.mergeStateStatus -notmatch "CLEAN|HAS_HOOKS|UNSTABLE") {
        $ready = $false
        $blockers += "Merge state is $($viewJson.mergeStateStatus)"
    }

    if ($ready) {
        Write-Host "PR #$prNumber is ready for merging."
        gh pr merge $prNumber --merge --delete-branch=false
        return
    } else {
        Write-Host "PR #$prNumber not ready yet: $($blockers -join ', ')"
        Start-Sleep -Seconds $interval
    }
}

Write-Host "Timeout reached. Blockers: $($blockers -join ', ')"
