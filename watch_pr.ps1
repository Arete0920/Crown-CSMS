$maxAttempts = 40
$interval = 60
$prNumber = 814

for ($i = 1; $i -le $maxAttempts; $i++) {
    Write-Host "--- Cycle $i (07:49:13) ---"
    $checks = gh pr checks $prNumber 2>&1 | Out-String
    $viewJson = gh pr view $prNumber --json mergeStateStatus,isDraft,reviewDecision,headRefName,baseRefName,url 2>&1 | Out-String
    try {
        $view = $viewJson | ConvertFrom-Json
    } catch {
        Write-Host "Error parsing JSON view"
        Write-Host $viewJson
        continue
    }
    
    $mergeStatus = $view.mergeStateStatus
    Write-Host "MergeStateStatus: $mergeStatus"
    
    $accountingPass = ($checks -match "accounting-verification\s+pass")
    $proofPass = ($checks -match "proof-ceremony\s+pass")
    
    $codeQLLines = $checks -split "[\r\n]+" | Where-Object { $_.Contains("CodeQL") }
    $codeQLPass = $false
    if ($codeQLLines.Count -gt 0) {
        $codeQLPass = $true
        foreach ($line in $codeQLLines) {
            if ($line -notmatch "(pass|✓|success)") {
                $codeQLPass = $false
                break
            }
        }
    }
    
    # Requirement 4: no required check is pending (*), fail (X), or cancel/error
    # Skip (-) is allowed.
    $anyFailingOrPending = ($checks -match "[\*X]\s+")
    
    # Requirement 5: CLEAN/HAS_HOOKS/UNSTABLE acceptable. Reject BLOCKED/DIRTY/BEHIND.
    $mergeable = ($mergeStatus -in "CLEAN", "HAS_HOOKS", "UNSTABLE")
    
    Write-Host "Found Flags -> accountingPass: $accountingPass, proofPass: $proofPass, codeQLPass: $codeQLPass, anyFailingOrPending: $anyFailingOrPending, mergeable: $mergeable"
    
    if ($accountingPass -and $proofPass -and $codeQLPass -and -not $anyFailingOrPending -and $mergeable) {
        Write-Host "PR $prNumber is READY for merge."
        gh pr merge $prNumber --merge --delete-branch=false
        Write-Host "Merge command executed."
        return
    }
    
    if ($i -eq $maxAttempts) {
        Write-Host "Reached max attempts. Latest checks output:"
        Write-Host $checks
        return
    }
    
    Write-Host "Conditions not met. Waiting $interval seconds..."
    Start-Sleep -Seconds $interval
}
