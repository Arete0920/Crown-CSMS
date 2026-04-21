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
