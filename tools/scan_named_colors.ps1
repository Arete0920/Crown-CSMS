$pagesDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"
# Named CSS color keywords in JS string context (excluding html comments)
$patterns = @('"white"', '"black"', '"crimson"', '"transparent"')
$total = 0
Get-ChildItem "$pagesDir\*.jsx" | ForEach-Object {
  $file = $_
  foreach ($p in $patterns) {
    $hits = (Select-String -Path $file.FullName -Pattern ([regex]::Escape($p)) -AllMatches).Matches.Count
    if ($hits -gt 0) {
      Write-Host "$($file.Name) — $p : $hits"
      $total += $hits
    }
  }
}
Write-Host ""
Write-Host "Total named color hits: $total"
