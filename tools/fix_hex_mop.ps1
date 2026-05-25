param()

$srcDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src"

$files = Get-ChildItem "$srcDir\*.jsx" -Recurse | Where-Object { $_.Name -ne "LoginPage.jsx" }
$n = 0
foreach ($f in $files) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # ── Standalone quoted hex ───────────────────────────────────────────────────
  $standalone = @(
    @("#d1d5db", "var(--crown-border)"),   # Tailwind gray-300
    @("#e2e8f0", "var(--crown-border)"),   # Tailwind slate-200
    @("#f1f5f9", "var(--crown-surface-2)"),# Tailwind slate-100
    @("#f8fafc", "var(--crown-surface-2)"),# Tailwind slate-50
    @("#fef2f2", "var(--crown-danger-bg)"),# very light red bg
    @("#fee2e2", "var(--crown-danger-bg)"),# another light red
    @("#fca5a5", "var(--crown-danger)"),   # danger border (red-300)
    @("#b91c1c", "var(--crown-danger)"),   # dark red
    @("#991b1b", "var(--crown-danger)"),   # darker red
    @("#86efac", "var(--crown-ok)"),       # ok border (green-200)
    @("#166534", "var(--crown-ok)"),       # same as --crown-ok value
    @("#3b82f6", "var(--crown-brand)"),    # blue-500
    @("#1890ff", "var(--crown-brand)"),    # Ant Design blue
    @("#fffacd", "var(--crown-warn-bg)"),  # lemon chiffon yellow
    @("#ffb3b3", "var(--crown-danger-bg)"),# light pink/red error text bg
    @("#f1d88a", "var(--crown-gold)")      # gold-2 fallback -> crown-gold
  )
  foreach ($p in $standalone) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # ── Embedded hex in solid borders ───────────────────────────────────────────
  $embeddedBorder = @("#d1d5db","#e2e8f0","#f1f5f9","#f8fafc")
  $embeddedDanger = @("#fca5a5","#c00","#dc2626","#cc0000","#b91c1c","#c62828")
  $embeddedOk     = @("#86efac","#2e7d32","#166534","#388e3c","#34a853","#16a34a")
  $embeddedWarn   = @("#f60","#f59e0b")

  foreach ($h in $embeddedBorder) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-border)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-border)'")
  }
  foreach ($h in $embeddedDanger) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-danger)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-danger)'")
  }
  foreach ($h in $embeddedOk) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-ok)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-ok)'")
  }
  foreach ($h in $embeddedWarn) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-warn)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-warn)'")
  }

  # ── Strip fallbacks from DEFINED vars inside border shorthand strings ────────
  # "1px solid var(--crown-border, #eee)" → "1px solid var(--crown-border)"
  $definedVarFallbacks = @(
    @('var(--crown-border, #eee)',   'var(--crown-border)'),
    @('var(--crown-border, #ddd)',   'var(--crown-border)'),
    @('var(--crown-border, #ccc)',   'var(--crown-border)'),
    @('var(--crown-border, #e5e7eb)','var(--crown-border)'),
    @('var(--crown-surface, #fff)',   'var(--crown-surface)'),
    @('var(--crown-surface, #ffffff)','var(--crown-surface)'),
    @('var(--crown-muted, #666)',     'var(--crown-muted)'),
    @('var(--crown-danger, #c0392b)','var(--crown-danger)'),
    @('var(--crown-danger, #dc2626)','var(--crown-danger)'),
    @('var(--crown-success-border, #b7dfb7)', 'var(--crown-ok)'),
    @('var(--crown-success, #16a34a)', 'var(--crown-ok)'),
    @('var(--crown-gold-2, #f1d88a)', 'var(--crown-gold)')
  )
  foreach ($p in $definedVarFallbacks) {
    # Replace wherever they appear (including inside border shorthand strings)
    $c = $c.Replace($p[0], $p[1])
  }

  # ── Standalone borderColor / ternary patterns ────────────────────────────────
  # e.g. borderColor: idx === current ? "var(--crown-brand)" : "#d1d5db"
  $c = $c.Replace(': "#d1d5db"', ': "var(--crown-border)"')
  $c = $c.Replace(": '#d1d5db'", ": 'var(--crown-border)'")

  if ($c -ne $orig) {
    [System.IO.File]::WriteAllText($f.FullName, $c, [System.Text.Encoding]::UTF8)
    $n++
    Write-Host "Updated: $($f.Name)"
  }
}
Write-Host ""
Write-Host "Mopping-up pass: $n file(s) updated."
