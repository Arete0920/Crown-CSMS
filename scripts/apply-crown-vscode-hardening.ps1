$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath "." ).Path + "\" + $Path, $Content, $enc)
}

function Backup-IfExists {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (Test-Path $Path) {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        Copy-Item $Path "$Path.bak.$stamp" -Force
    }
}

Write-Host "Applying Crown VS Code hardening..." -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
    Write-Warning "No .git folder found in current directory. Make sure you are running this from the repo root."
}

New-Item -ItemType Directory -Force -Path ".vscode" | Out-Null
New-Item -ItemType Directory -Force -Path "scripts" | Out-Null

$editorConfig = @'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.ps1]
end_of_line = crlf
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
'@

$settingsJson = @'
{
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.trimFinalNewlines": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "editor.rulers": [100],
  "editor.minimap.enabled": false,
  "editor.renderWhitespace": "selection",
  "editor.stickyScroll.enabled": true,
  "explorer.excludeGitIgnore": true,
  "files.exclude": {
    "**/.DS_Store": true,
    "**/Thumbs.db": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/coverage": true,
    "**/htmlcov": true,
    "**/AUDIT_PACK_*": true,
    "**/audit-artifacts/**": true,
    "**/artifacts/**": true,
    "**/ci.sqlite3": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/coverage": true,
    "**/htmlcov": true,
    "**/audit-artifacts/**": true,
    "**/artifacts/**": true,
    "**/AUDIT_PACK_*": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "prettier.requireConfig": true,
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.analysis.typeCheckingMode": "basic",
  "python.terminal.activateEnvironment": true,
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": [
        "-NoLogo",
        "-NoProfile"
      ]
    }
  },
  "yaml.validate": true,
  "yaml.format.enable": true,
  "git.enableSmartCommit": false,
  "git.confirmSync": true,
  "git.autofetch": true,
  "problems.showCurrentInStatus": true,
  "scm.diffDecorations": "all"
}
'@

$extensionsJson = @'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "redhat.vscode-yaml",
    "editorconfig.editorconfig",
    "eamodio.gitlens",
    "github.vscode-pull-request-github",
    "humao.rest-client"
  ],
  "unwantedRecommendations": [
    "vivaxy.vscode-conventional-commits",
    "ms-vscode.powershell-preview",
    "ms-azuretools.vscode-azureappservice",
    "ms-azuretools.vscode-azureresourcegroups",
    "oderwat.indent-rainbow"
  ]
}
'@

$tasksJson = @'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "deep-audit: bootstrap",
      "type": "shell",
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "audit-artifacts\\deep-audit\\bootstrap.ps1"
      ],
      "problemMatcher": []
    },
    {
      "label": "deep-audit: inventory",
      "type": "shell",
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "audit-artifacts\\deep-audit\\inventory.ps1"
      ],
      "problemMatcher": []
    },
    {
      "label": "deep-audit: static scans",
      "type": "shell",
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "audit-artifacts\\deep-audit\\static_scans.ps1"
      ],
      "problemMatcher": []
    },
    {
      "label": "deep-audit: runtime checks",
      "type": "shell",
      "command": "powershell",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "audit-artifacts\\deep-audit\\runtime_checks.ps1"
      ],
      "problemMatcher": []
    }
  ]
}
'@

$setupProfilePs1 = @'
$ErrorActionPreference = "Stop"

$ProfileName = "Crown Reset"

$Keep = @(
  "ms-python.python",
  "ms-python.vscode-pylance",
  "dbaeumer.vscode-eslint",
  "esbenp.prettier-vscode",
  "redhat.vscode-yaml",
  "editorconfig.editorconfig",
  "eamodio.gitlens",
  "github.vscode-pull-request-github",
  "humao.rest-client"
)

$RemoveFromProfile = @(
  "vivaxy.vscode-conventional-commits",
  "ms-vscode.powershell-preview",
  "ms-azuretools.vscode-azureappservice",
  "ms-azuretools.vscode-azureresourcegroups",
  "oderwat.indent-rainbow"
)

function Get-CodeCli {
  $cmd = Get-Command code.cmd -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  $fallback = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
  if (Test-Path $fallback) {
    return $fallback
  }

  throw "VS Code CLI 'code.cmd' was not found."
}

$CodeCli = Get-CodeCli
& $CodeCli --version | Out-Null

Write-Host "Creating / refreshing VS Code profile: $ProfileName"

foreach ($ext in $Keep) {
  Write-Host "Installing $ext into profile '$ProfileName'..."
  & $CodeCli --profile $ProfileName --install-extension $ext --force
}

foreach ($ext in $RemoveFromProfile) {
  Write-Host "Removing $ext from profile '$ProfileName' if present..."
  & $CodeCli --profile $ProfileName --uninstall-extension $ext
}

Write-Host ""
Write-Host "Done."
Write-Host "Next:"
Write-Host "1. Open the repo with: code . --profile `"$ProfileName`""
Write-Host "2. Reload VS Code."
'@

$gitignoreBlock = @'

# >>> Crown VS Code hardening block >>>
.vscode/*.log
.vscode/*.tmp

# Python
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
coverage.xml

# Node / frontend
node_modules/
dist/
build/
coverage/

# Local databases / temp runtime files
ci.sqlite3
*.sqlite3
_tmp_*/
_PHASE*/
*.pid
*.seed

# Audit / evidence / generated artifacts
AUDIT_PACK_*/
audit-artifacts/
artifacts/
docs/audit/evidence/
docs/audit/reports/
docs/status/

# OS noise
.DS_Store
Thumbs.db
# <<< Crown VS Code hardening block <<<
'@

Backup-IfExists ".editorconfig"
Backup-IfExists ".vscode\settings.json"
Backup-IfExists ".vscode\extensions.json"
Backup-IfExists ".vscode\tasks.json"
Backup-IfExists "scripts\setup-crown-reset-profile.ps1"
if (Test-Path ".gitignore") {
    Backup-IfExists ".gitignore"
}

Write-Utf8NoBom -Path ".editorconfig" -Content $editorConfig
Write-Utf8NoBom -Path ".vscode\settings.json" -Content $settingsJson
Write-Utf8NoBom -Path ".vscode\extensions.json" -Content $extensionsJson
Write-Utf8NoBom -Path ".vscode\tasks.json" -Content $tasksJson
Write-Utf8NoBom -Path "scripts\setup-crown-reset-profile.ps1" -Content $setupProfilePs1

if (-not (Test-Path ".gitignore")) {
    Write-Utf8NoBom -Path ".gitignore" -Content $gitignoreBlock.TrimStart("`r", "`n")
}
else {
    $existing = Get-Content ".gitignore" -Raw
    if ($existing -notmatch [regex]::Escape("# >>> Crown VS Code hardening block >>>")) {
        $newContent = $existing.TrimEnd() + "`r`n" + $gitignoreBlock
        Write-Utf8NoBom -Path ".gitignore" -Content $newContent
    }
    else {
        Write-Host ".gitignore already contains the Crown hardening block."
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Files written:"
Write-Host "  .editorconfig"
Write-Host "  .vscode\settings.json"
Write-Host "  .vscode\extensions.json"
Write-Host "  .vscode\tasks.json"
Write-Host "  scripts\setup-crown-reset-profile.ps1"
Write-Host "  .gitignore updated"
Write-Host ""
Write-Host "Next commands:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup-crown-reset-profile.ps1"
Write-Host "  code . --profile `"Crown Reset`""
