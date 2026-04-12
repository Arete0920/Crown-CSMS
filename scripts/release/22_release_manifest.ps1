$ErrorActionPreference = "Stop"

$base = "audit-artifacts\release-manifest"
New-Item -ItemType Directory -Force -Path $base | Out-Null

git rev-parse --show-toplevel | Out-File "$base\00_repo_root.txt"
git branch --show-current | Out-File "$base\01_current_branch.txt"
git rev-parse HEAD | Out-File "$base\02_head_sha.txt"
git tag --sort=-creatordate | Out-File "$base\03_tags.txt"
git status --short | Out-File "$base\04_status.txt"
git log --oneline -20 | Out-File "$base\05_recent_commits.txt"

Get-ChildItem .github\workflows -File -ErrorAction SilentlyContinue |
  Select-Object Name, FullName |
  ConvertTo-Json -Depth 5 |
  Out-File "$base\06_workflows.json" -Encoding utf8

Get-ChildItem docs\release -File -ErrorAction SilentlyContinue |
  Select-Object Name, FullName |
  ConvertTo-Json -Depth 5 |
  Out-File "$base\07_release_docs.json" -Encoding utf8

Write-Host "Release manifest written to $base"