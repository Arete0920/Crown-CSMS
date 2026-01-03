# backend\runserver_watch.ps1
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$pythonExe = ".\venv\Scripts\python.exe"
$managerPy = "manage.py"

while ($true) {
  Write-Host "Starting Django server..." -ForegroundColor Cyan
  & $pythonExe $managerPy runserver 127.0.0.1:8000
  Write-Host "Server stopped/crashed. Restarting in 2 seconds..." -ForegroundColor Yellow
  Start-Sleep -Seconds 2
}
