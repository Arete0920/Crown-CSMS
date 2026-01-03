# backend\runserver.ps1
# Runs Django development server with proper process isolation to prevent immediate exit
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Always use venv python, never "python"
$py = ".\venv\Scripts\python.exe"

if (!(Test-Path $py)) {
  Write-Host "ERROR: venv not found at backend\venv. Create it first." -ForegroundColor Red
  exit 1
}

Write-Host "Checking Python environment..." -ForegroundColor Cyan
& $py -c "import sys; print('Python:', sys.executable)"

Write-Host "`nRunning migrations..." -ForegroundColor Cyan
& $py manage.py migrate

Write-Host "`nStarting Django development server..." -ForegroundColor Green
Write-Host "Server will run at http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Press CTRL+C in this terminal to stop the server" -ForegroundColor Yellow
Write-Host ""

# Use Start-Process with -Wait to keep the server in foreground but isolated from terminal signals
$process = Start-Process -FilePath $py `
    -ArgumentList "manage.py", "runserver", "127.0.0.1:8000", "--noreload" `
    -WorkingDirectory $PSScriptRoot `
    -NoNewWindow `
    -PassThru `
    -Wait

if ($process.ExitCode -ne 0) {
    Write-Host "Server exited with code: $($process.ExitCode)" -ForegroundColor Red
    exit $process.ExitCode
}
