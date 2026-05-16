$prNumber = "814"
$maxRuntimeMinutes = 45
$intervalSeconds = 60
$startTime = Get-Date

Write-Host "Monitoring PR #$prNumber for up to $maxRuntimeMinutes minutes..."

while (((Get-Date) - $startTime).TotalMinutes -lt $maxRuntimeMinutes) {
    $checksJson = gh pr checks $prNumber --json name,state,bucket,workflow,link
    $checks = $checksJson | ConvertFrom-Json
    
    $viewJson = gh pr view $prNumber --json mergeStateStatus,isDraft,reviewDecision,url
    $view = $viewJson | ConvertFrom-Json

    $pending = $checks | Where-Object { $_.state -in @('PENDING', 'IN_PROGRESS', 'QUEUED', 'WAITING') }
    $failed = $checks | Where-Object { $_.state -in @('FAILURE', 'ERROR', 'CANCELLED', 'TIMED_OUT', 'ACTION_REQUIRED') }
    $allFinished = ($pending.Count -eq 0)

    Write-Host "$(Get-Date -Format 'HH:mm:ss') - Pending: $($pending.Count), Failed: $($failed.Count), MergeStatus: $($view.mergeStateStatus)"

    if ($allFinished) {
        if ($failed.Count -eq 0) {
            $mergeableStates = @('CLEAN', 'HAS_HOOKS', 'UNSTABLE')
            if ($mergeableStates -contains $view.mergeStateStatus) {
                Write-Host "All checks passed and PR is mergeable. Attempting merge..."
                gh pr merge $prNumber --merge --delete-branch=false
                return
            } else {
                Write-Host "All checks passed but PR status is '$($view.mergeStateStatus)'. Waiting for mergeability..."
            }
        } else {
            Write-Host "Checks finished with failures:"
            $failed | Select-Object name, link | Format-Table -AutoSize
            return
        }
    }

    Start-Sleep -Seconds $intervalSeconds
}

Write-Host "Timeout reached after $maxRuntimeMinutes minutes."
