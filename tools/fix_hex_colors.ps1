param()

$pagesDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"

$pairs6 = @(
  @("#dc2626","var(--crown-danger)"), @("#c62828","var(--crown-danger)"), @("#cc0000","var(--crown-danger)"),
  @("#f44336","var(--crown-danger)"), @("#ef4444","var(--crown-danger)"),
  @("#ffebee","var(--crown-danger-bg)"), @("#ffe6e6","var(--crown-danger-bg)"), @("#fce8e8","var(--crown-danger-bg)"),
  @("#f59e0b","var(--crown-warn)"), @("#efb100","var(--crown-warn)"), @("#ffa726","var(--crown-warn)"),
  @("#fff3cd","var(--crown-warn-bg)"), @("#fffbf0","var(--crown-warn-bg)"), @("#fff9c4","var(--crown-warn-bg)"),
  @("#fef9c3","var(--crown-warn-bg)"), @("#fff8e1","var(--crown-warn-bg)"),
  @("#1b5e20","var(--crown-ok)"), @("#2e7d32","var(--crown-ok)"), @("#1a7f37","var(--crown-ok)"),
  @("#388e3c","var(--crown-ok)"), @("#15803d","var(--crown-ok)"), @("#00cc00","var(--crown-ok)"),
  @("#10b981","var(--crown-ok)"), @("#34a853","var(--crown-ok)"), @("#1a5c2a","var(--crown-ok)"),
  @("#e8f5e9","var(--crown-ok-bg)"), @("#e6ffe6","var(--crown-ok-bg)"), @("#e6f4ea","var(--crown-ok-bg)"),
  @("#d1fae5","var(--crown-ok-bg)"),
  @("#1565c0","var(--crown-brand)"), @("#0066cc","var(--crown-brand)"), @("#2563eb","var(--crown-brand)"),
  @("#1976d2","var(--crown-brand)"),
  @("#6b7280","var(--crown-muted)"), @("#9ca3af","var(--crown-muted)"),
  @("#374151","var(--crown-ink)"), @("#111827","var(--crown-ink)"),
  @("#e5e7eb","var(--crown-border)"), @("#e0e0e0","var(--crown-border)"),
  @("#f9f9f9","var(--crown-surface-2)"), @("#fafafa","var(--crown-surface-2)"), @("#f5f5f5","var(--crown-surface-2)"),
  @("#f9fafb","var(--crown-surface-2)"), @("#f3f4f6","var(--crown-surface-2)"), @("#f0f0f0","var(--crown-surface-2)"),
  @("#f0f8ff","var(--crown-surface-2)")
)

$pairs3 = @(
  @("#ddd","var(--crown-border)"), @("#eee","var(--crown-border)"), @("#ccc","var(--crown-border)"),
  @("#fff","var(--crown-surface)"),
  @("#666","var(--crown-muted)"), @("#555","var(--crown-muted)"), @("#777","var(--crown-muted)"),
  @("#888","var(--crown-muted)"), @("#999","var(--crown-muted)"),
  @("#333","var(--crown-ink)")
)

# Also fix: var(--color-error, #f44336) and var(--color-success, #388e3c) patterns
# And: "white" as a string color value
$exactPairs = @(
  @('var(--color-error, #f44336)', 'var(--crown-danger)'),
  @('var(--color-success, #388e3c)', 'var(--crown-ok)'),
  @("= `"white`"", "= `"var(--crown-surface)`""),
  @("= 'white'", "= 'var(--crown-surface)'")
)

$files = Get-ChildItem "$pagesDir\*.jsx" | Where-Object { $_.Name -ne "LoginPage.jsx" }
$n = 0
foreach ($f in $files) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # 6-char pairs
  foreach ($p in $pairs6) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # 3-char pairs
  foreach ($p in $pairs3) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # Exact string pairs
  foreach ($p in $exactPairs) {
    $c = $c.Replace($p[0], $p[1])
  }

  if ($c -ne $orig) {
    [System.IO.File]::WriteAllText($f.FullName, $c, [System.Text.Encoding]::UTF8)
    $n++
    Write-Host "Updated: $($f.Name)"
  }
}
Write-Host ""
Write-Host "Total: $n file(s) updated."
