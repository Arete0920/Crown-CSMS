$ErrorActionPreference = "Stop"

$dest = "artifacts\root-residue\$(Get-Date -Format yyyyMMdd_HHmmss)"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$allow = @(
  ".github","artifacts","backend","contracts","core_shadowed","crown2026_config","docs","frontend",
  "scripts","services","tests","tools",
  ".gitignore",".editorconfig",".gitattributes",
  "README.md","CONTRIBUTING.md","SECURITY.md","NOTICE.md","CHANGELOG.md","COMPLIANCE.md",
  "CODEOWNERS","VERSION","manage.py","pytest.ini","requirements.txt","docker-compose.yml","package.json","package-lock.json"
)

$manifest = @()
Get-ChildItem -Force | ForEach-Object {
  if ($allow -contains $_.Name) { return }
  if ($_.Name -eq ".git") { return }
  $target = Join-Path $dest $_.Name
  Move-Item -Force $_.FullName $target
  $manifest += [pscustomobject]@{ name = $_.Name; moved_to = $target }
}

$manifest | ConvertTo-Json -Depth 5 | Out-File "$dest\cleanup_manifest.json" -Encoding utf8
Write-Host "Root residue cleanup complete: $dest"