# backend\ping.ps1
try {
  $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/director/aid/summary/ -TimeoutSec 2 -MaximumRedirection 0
  Write-Host "UP: $($r.StatusCode)" -ForegroundColor Green
} catch {
  Write-Host "DOWN: 127.0.0.1:8000" -ForegroundColor Red
}

