param()

$srcDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src"

# Additional color pairs not covered before
$pairs6Extra = @(
  # Tailwind Slate palette
  @("#e2e8f0", "var(--crown-border)"),   # slate-200
  @("#1e293b", "var(--crown-ink)"),       # slate-800
  @("#0f172a", "var(--crown-ink)"),       # slate-950
  @("#f1f5f9", "var(--crown-surface-2)"), # slate-100
  @("#64748b", "var(--crown-muted)"),     # slate-500
  @("#f8fafc", "var(--crown-surface-2)"), # slate-50
  @("#475569", "var(--crown-muted)"),     # slate-600
  @("#94a3b8", "var(--crown-muted)"),     # slate-400
  @("#cbd5e1", "var(--crown-border)"),    # slate-300
  @("#1e40af", "var(--crown-brand)"),     # (same as --crown-info but using brand)
  # Material/other green
  @("#4CAF50", "var(--crown-ok)"),
  @("#4caf50", "var(--crown-ok)"),
  @("#2d7a2d", "var(--crown-ok)"),
  @("#16a34a", "var(--crown-ok)"),
  @("#b7dfb7", "var(--crown-ok)"),        # success border fallback color
  @("#f0faf0", "var(--crown-ok-bg)"),     # success bg fallback color
  @("#f0fdf4", "var(--crown-ok-bg)"),     # another success bg
  # Misc  
  @("#856404", "var(--crown-warn)"),      # dark amber
  @("#fff4e6", "var(--crown-warn-bg)"),   # light orange bg
  @("#f8f9fa", "var(--crown-surface-2)"), # Bootstrap light
  @("#e8f4fd", "var(--crown-surface-2)"), # light blue surface
  @("#c0392b", "var(--crown-danger)"),    # slightly different danger red
  @("#1a73e8", "var(--crown-brand)")      # Google blue variant
)

$pairs3Extra = @(
  @("#f60", "var(--crown-warn)"),         # short orange = ff6600
  @("#f8f", "var(--crown-ok-bg)"),        # unlikely but for safety
  @("#f1d", "var(--crown-warn-bg)")       # unlikely but for safety
)

# CSS var consolidation: replace undefined/incorrect vars with defined ones
# Pattern: entire var(--crown-xxx, #yyy) → var(--crown-defined)
$varConsolidations = @(
  # Undefined success variants → ok
  @('var(--crown-success-bg, #f0faf0)',   'var(--crown-ok-bg)'),
  @('var(--crown-success-bg, #f0fdf4)',   'var(--crown-ok-bg)'),
  @('var(--crown-success-border, #b7dfb7)', 'var(--crown-ok)'),
  @('var(--crown-success, #2d7a2d)',      'var(--crown-ok)'),
  @('var(--crown-success, #16a34a)',      'var(--crown-ok)'),
  @('var(--crown-success, #2e7d32)',      'var(--crown-ok)'),
  # Undefined error variants → danger
  @('var(--crown-error, #dc2626)',        'var(--crown-danger)'),
  @('var(--crown-error, #c0392b)',        'var(--crown-danger)'),
  @('var(--crown-error, #f44336)',        'var(--crown-danger)'),
  # Defined vars — strip unnecessary fallbacks
  @('var(--crown-danger, #c0392b)',       'var(--crown-danger)'),
  @('var(--crown-danger, #dc2626)',       'var(--crown-danger)'),
  @('var(--crown-border, #eee)',          'var(--crown-border)'),
  @('var(--crown-border, #ddd)',          'var(--crown-border)'),
  @('var(--crown-border, #ccc)',          'var(--crown-border)'),
  @('var(--crown-surface, #f8f9fa)',      'var(--crown-surface)'),
  @('var(--crown-surface, #fff)',         'var(--crown-surface)'),
  @('var(--crown-muted, #666)',           'var(--crown-muted)'),
  # Undefined primary/accent variants
  @('var(--crown-primary-bg, #f0f7ff)',   'var(--crown-surface-2)'),
  @('var(--crown-accent-light, #e8f4fd)', 'var(--crown-surface-2)'),
  @('var(--crown-accent, #1a73e8)',       'var(--crown-brand)'),
  # info fallback → keep but simplify if var is defined
  @('var(--crown-info, #5aa9e6)',         'var(--crown-info)')
)

$files = Get-ChildItem "$srcDir\*.jsx" -Recurse | Where-Object { $_.Name -ne "LoginPage.jsx" }
$n = 0
foreach ($f in $files) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # Extra 6-char pairs
  foreach ($p in $pairs6Extra) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # Extra 3-char pairs
  foreach ($p in $pairs3Extra) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # Also handle #4CAF50 embedded in border context
  $c = $c.Replace('solid #4CAF50"', 'solid var(--crown-ok)"')
  $c = $c.Replace("solid #4CAF50'", "solid var(--crown-ok)'")
  $c = $c.Replace('solid #4caf50"', 'solid var(--crown-ok)"')
  $c = $c.Replace("solid #4caf50'", "solid var(--crown-ok)'")

  # Consolidate CSS vars (replace undefined or redundant var() calls)
  foreach ($p in $varConsolidations) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  if ($c -ne $orig) {
    [System.IO.File]::WriteAllText($f.FullName, $c, [System.Text.Encoding]::UTF8)
    $n++
    Write-Host "Updated: $($f.Name)"
  }
}
Write-Host ""
Write-Host "Final pass: $n file(s) updated."
