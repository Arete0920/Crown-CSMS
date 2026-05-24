param()

# Target the entire src directory, not just pages
$srcDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src"

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
  @("#1976d2","var(--crown-brand)"), @("#007bff","var(--crown-brand)"), @("#1890ff","var(--crown-brand)"),
  @("#6b7280","var(--crown-muted)"), @("#9ca3af","var(--crown-muted)"),
  @("#374151","var(--crown-ink)"), @("#111827","var(--crown-ink)"),
  @("#e5e7eb","var(--crown-border)"), @("#e0e0e0","var(--crown-border)"),
  @("#f9f9f9","var(--crown-surface-2)"), @("#fafafa","var(--crown-surface-2)"), @("#f5f5f5","var(--crown-surface-2)"),
  @("#f9fafb","var(--crown-surface-2)"), @("#f3f4f6","var(--crown-surface-2)"), @("#f0f0f0","var(--crown-surface-2)"),
  @("#f0f8ff","var(--crown-surface-2)"), @("#e3f2fd","var(--crown-surface-2)")
)

$pairs3 = @(
  @("#ddd","var(--crown-border)"), @("#eee","var(--crown-border)"), @("#ccc","var(--crown-border)"),
  @("#bbb","var(--crown-border)"),
  @("#fff","var(--crown-surface)"),
  @("#c00","var(--crown-danger)"),
  @("#666","var(--crown-muted)"), @("#555","var(--crown-muted)"), @("#777","var(--crown-muted)"),
  @("#888","var(--crown-muted)"), @("#999","var(--crown-muted)"),
  @("#333","var(--crown-ink)")
)

# Embedded hex inside CSS multi-value strings like "1px solid #ccc"
$embeddedBorderHex = @("#ddd","#eee","#ccc","#bbb","#e0e0e0","#e5e7eb","#f0f0f0","#f3f4f6","#999")
$embeddedOkHex     = @("#34a853","#00cc00","#10b981","#2e7d32","#1a7f37","#388e3c","#15803d","#1b5e20","#1a5c2a")
$embeddedDangerHex = @("#cc0000","#c62828","#dc2626")
$embeddedBrandHex  = @("#1976d2","#1565c0","#0066cc","#2563eb","#007bff","#1890ff")
$embeddedInkHex    = @("#333")

# Exact string replacements
$exactPairs = @(
  @('var(--color-error, #f44336)', 'var(--crown-danger)'),
  @('var(--color-success, #388e3c)', 'var(--crown-ok)')
)

# Files to process — all JSX files EXCEPT LoginPage.jsx
$files = Get-ChildItem "$srcDir\*.jsx" -Recurse | Where-Object { $_.Name -ne "LoginPage.jsx" }
$n = 0
foreach ($f in $files) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # 6-char pairs (standalone quotes)
  foreach ($p in $pairs6) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # 3-char pairs (standalone quotes)
  foreach ($p in $pairs3) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # Embedded hex in CSS shorthand (border/outline values)
  foreach ($h in $embeddedBorderHex) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-border)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-border)'")
  }
  foreach ($h in $embeddedOkHex) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-ok)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-ok)'")
  }
  foreach ($h in $embeddedDangerHex) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-danger)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-danger)'")
  }
  foreach ($h in $embeddedBrandHex) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-brand)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-brand)'")
  }
  foreach ($h in $embeddedInkHex) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-ink)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-ink)'")
  }

  # Exact string replacements
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
Write-Host "Full-src pass: $n file(s) updated."
