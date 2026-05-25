$pagesDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"
$pattern = '"#[0-9a-fA-F]{3,6}"|''#[0-9a-fA-F]{3,6}'''
$total = 0
Get-ChildItem "$pagesDir\*.jsx" | ForEach-Object {
  $hits = (Select-String -Path $_.FullName -Pattern $pattern -AllMatches).Matches.Count
  if ($hits -gt 0) {
    Write-Host "$($_.Name): $hits hits"
    $total += $hits
  }
}
Write-Host ""
Write-Host "Total remaining hits: $total"
