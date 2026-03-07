param()

$pagesDir = "c:\Users\JMega\OneDrive\Desktop\Crown2026\frontend\dashboards\src\pages"

# Standalone missed hex values (quoted)
$standalone = @(
  @("#c00",    "var(--crown-danger)"),
  @("#e3f2fd", "var(--crown-surface-2)")
)

# Embedded hex inside CSS multi-value strings like "1px solid #ccc"
# Replace the hex portion within these patterns
$embeddedBorder = @("#ddd", "#eee", "#ccc", "#e0e0e0", "#e5e7eb", "#f0f0f0", "#f3f4f6", "#999")
$embeddedInk    = @("#333")

$files = Get-ChildItem "$pagesDir\*.jsx" | Where-Object { $_.Name -ne "LoginPage.jsx" }
$n = 0
foreach ($f in $files) {
  $c = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
  $orig = $c

  # Fix standalone quoted #c00 and #e3f2fd
  foreach ($p in $standalone) {
    $c = $c.Replace('"' + $p[0] + '"', '"' + $p[1] + '"')
    $c = $c.Replace("'" + $p[0] + "'", "'" + $p[1] + "'")
  }

  # Fix embedded border colors: "solid #xxx" → "solid var(--crown-border)"
  foreach ($h in $embeddedBorder) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-border)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-border)'")
  }

  # Fix embedded ink colors: "solid #333" → "solid var(--crown-ink)"
  foreach ($h in $embeddedInk) {
    $c = $c.Replace("solid $h`"", "solid var(--crown-ink)`"")
    $c = $c.Replace("solid $h'",  "solid var(--crown-ink)'")
  }

  # Also fix "transparent" when used as a bg color (not border)
  # e.g. background: "transparent" — this is fine actually, transparent is not a hex color.
  # Leave transparent alone.

  if ($c -ne $orig) {
    [System.IO.File]::WriteAllText($f.FullName, $c, [System.Text.Encoding]::UTF8)
    $n++
    Write-Host "Updated: $($f.Name)"
  }
}
Write-Host ""
Write-Host "Second pass: $n file(s) updated."
