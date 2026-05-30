$base='https://crown-api-prod.azurewebsites.net'
$tests=@('/api/dashboard/me','/api/admissions/summary','/api/finance/summary')
foreach($p in $tests){
  Write-Host "=== NO AUTH $p ==="
  curl.exe -sS -i "$base$p" | Select-Object -First 25
  Write-Host "`n=== FAKE AUTH NO TENANT $p ==="
  curl.exe -sS -i -H "Authorization: Bearer fake-token" "$base$p" | Select-Object -First 25
  Write-Host "`n=== FAKE AUTH WRONG TENANT $p ==="
  curl.exe -sS -i -H "Authorization: Bearer fake-token" -H "X-School-Id: 00000000-0000-0000-0000-000000000000" "$base$p" | Select-Object -First 25
  Write-Host "`n"
}
