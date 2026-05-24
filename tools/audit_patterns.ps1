param(
  [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$hits = New-Object System.Collections.Generic.List[object]

$files = Get-ChildItem -Path $RepoRoot -Recurse -File |
  Where-Object {
    $_.FullName -notmatch "\\node_modules\\|\\\.git\\|\\dist\\|\\build\\|\\coverage\\|\\\.venv\\|\\venv\\|\\__pycache__\\|\\\.next\\|\\\.pytest_cache\\|\\\.mypy_cache\\|\\\.cache\\|\\\.tox\\" `
    -and $_.Length -lt 2MB `
    -and $_.Extension -notin @(".png",".jpg",".jpeg",".gif",".webp",".pdf",".zip",".7z",".exe",".dll",".pdb",".ico",".woff",".woff2",".ttf",".eot")
  }

$patterns = @(
  @{ Label="DEBUG_TRUE";             Re="(?i)\bDEBUG\s*=\s*True\b" },
  @{ Label="DEMO_MODE_TRUE";         Re="(?i)\bDEMO_MODE\s*=\s*True\b" },
  @{ Label="CORS_ALLOW_ALL";         Re="(?i)\bCORS_ALLOW_ALL_ORIGINS\s*=\s*True\b" },
  @{ Label="SECRET_KEY_INLINE";      Re="(?i)\bSECRET_KEY\s*=\s*['""][^'""]{20,}['""]" },
  @{ Label="PASSWORD_LITERAL";       Re="(?i)\b(password|passwd|pwd)\s*[:=]\s*['""][^'""]{6,}['""]" },
  @{ Label="PRIVATE_KEY";            Re="-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----" },
  @{ Label="AZURE_CONNSTRING";       Re="(?i)AccountKey=|SharedAccessKey=" },
  @{ Label="ALLOW_ANY_PERMISSION";   Re="(?i)\bAllowAny\b" },
  @{ Label="ALLOWED_HOSTS_WILDCARD"; Re="(?i)\bALLOWED_HOSTS\s*=\s*\[\s*['""\*]['""\*]?\s*\]" },
  @{ Label="CSRF_DISABLED";          Re="(?i)\bCSRF_COOKIE_SECURE\s*=\s*False\b" },
  @{ Label="TEMP_DIAGNOSTIC";        Re="(?i)\bdef\s+whoami\b|\bwhoami_endpoint\b" }
)

# Known intentional occurrences to suppress (file path substrings)
$suppressPaths = @(
  "audit_patterns.ps1",   # this file itself contains the patterns as strings
  "AUDIT",                # audit reports
  "PROOF"                 # proof notes
)

foreach ($f in $files) {
  $skip = $false
  foreach ($s in $suppressPaths) { if ($f.FullName -like "*$s*") { $skip = $true; break } }
  if ($skip) { continue }

  $text = $null
  try { $text = Get-Content $f.FullName -Raw -ErrorAction Stop } catch { continue }

  foreach ($p in $patterns) {
    if ($text -match $p.Re) {
      $lines = Select-String -Path $f.FullName -Pattern $p.Re -AllMatches -ErrorAction SilentlyContinue |
        Select-Object -First 3
      foreach ($m in $lines) {
        $hits.Add([PSCustomObject]@{
          Label = $p.Label
          File  = $f.FullName.Replace($RepoRoot, "").TrimStart("\")
          Line  = "L$($m.LineNumber): $($m.Line.Trim())"
        })
      }
    }
  }
}

if ($hits.Count -gt 0) {
  $hits | Sort-Object Label, File | Format-Table Label, File, Line -AutoSize -Wrap
  Write-Host ""
  Write-Host "HITS FOUND: $($hits.Count)" -ForegroundColor Yellow
  exit 2
} else {
  Write-Host "No high-risk patterns detected." -ForegroundColor Green
  exit 0
}
