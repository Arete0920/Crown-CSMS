<#
.SYNOPSIS
  Scans CROWN sandbox assets for common real-data risk patterns.

.DESCRIPTION
  This is a conservative static scanner for sandbox manifests, seed packs, docs, and frontend sandbox files.
  It is not a substitute for compliance review, but it catches obvious accidental data leakage risks.
#>

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Location).Path
$targets = @(
  "sandbox",
  "frontend/dashboards/src/sandbox",
  "frontend/dashboards/src/pages/SandboxLandingPage.jsx",
  "docs/compliance/SANDBOX_DATA_POLICY.md",
  "docs/product/GUIDED_PROOF_SANDBOX_BLUEPRINT.md"
)

$patterns = @(
  @{ Name = "Possible SSN"; Regex = "\b\d{3}-\d{2}-\d{4}\b" },
  @{ Name = "Possible credit card"; Regex = "\b(?:\d[ -]*?){13,16}\b" },
  @{ Name = "Possible production secret"; Regex = "(?i)(api[_-]?key|client[_-]?secret|bearer\s+[a-z0-9._-]+|refresh[_-]?token|private[_-]?key)" },
  @{ Name = "Non-demo email domain"; Regex = "(?i)[a-z0-9._%+-]+@(?!.*(example\.org|example\.com|example\.test|crown2026\.local))[a-z0-9.-]+\.[a-z]{2,}" },
  @{ Name = "Possible phone number"; Regex = "\b(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b" }
)

$findings = @()
foreach ($target in $targets) {
  $path = Join-Path $repoRoot $target
  if (-not (Test-Path $path)) { continue }
  $files = if ((Get-Item $path).PSIsContainer) {
    Get-ChildItem $path -Recurse -File | Where-Object { $_.Extension -match '\.(json|md|txt|js|jsx|ts|tsx)$' }
  } else {
    @(Get-Item $path)
  }

  foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    foreach ($pattern in $patterns) {
      $matches = [regex]::Matches($content, $pattern.Regex)
      foreach ($match in $matches) {
        $findings += [pscustomobject]@{
          File = $file.FullName.Replace($repoRoot + [IO.Path]::DirectorySeparatorChar, "")
          Type = $pattern.Name
          Match = $match.Value
        }
      }
    }
  }
}

if ($findings.Count -gt 0) {
  $findings | Format-Table -AutoSize
  throw "Sandbox no-real-data scan failed with $($findings.Count) finding(s). Review and clear before buyer-facing use."
}

Write-Host "PASS sandbox no-real-data scan found no obvious real-data risk patterns."
