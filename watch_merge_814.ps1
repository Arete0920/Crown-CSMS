$startTime = Get-Date
$timeout = 30 # minutes
$interval = 60 # seconds

while ((Get-Date) -lt $startTime.AddMinutes($timeout)) {
    Write-Host "Checking PR #814 status at $(Get-Date)..."
    $checks = gh pr checks 814 --json name,state,bucket,workflow,link | ConvertFrom-Json
    $view = gh pr view 814 --json mergeStateStatus,isDraft,reviewDecision,url | ConvertFrom-Json
    
    $unfinished = $checks | Where-Object { $_.state -in @('QUEUED', 'IN_PROGRESS') }
    $failed = $checks | Where-Object { $_.state -eq 'FAILURE' }
    
    Write-Host "- Unfinished: $($unfinished.Count)"
    Write-Host "- Failed: $($failed.Count)"
    Write-Host "- Merge status: $($view.mergeStateStatus)"
    
    if (-not $unfinished -and -not $failed -and ($view.mergeStateStatus -in @('CLEAN', 'HAS_HOOKS', 'UNSTABLE'))) {
        Write-Host "Conditions met. Attempting merge..."
        gh pr merge 814 --merge --delete-branch=false
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Merge successful."
            exit 0
        }
    }
    
    Start-Sleep -Seconds $interval
}

Write-Host "Timed out. Final status:"
$checks | Select-Object name, state | Format-Table
$view | Select-Object mergeStateStatus, reviewDecision
