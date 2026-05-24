$srcDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src"
$total = 0
Get-ChildItem "$srcDir\*.jsx" -Recurse | ForEach-Object {
  $hits = (Select-String -Path $_.FullName -Pattern '#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}').Count
  if ($hits -gt 0) {
    Write-Host "$($_.Name): $hits"
    $total += $hits
  }
}
if ($total -eq 0) {
  Write-Host "ALL CLEAN. Zero hex hits across entire src tree."
} else {
  Write-Host ""
  Write-Host "Total remaining: $total"
}
