param(
    [string]$ProfileName = "Crown Reset",
    [switch]$UseCurrentProfile,
    [switch]$WriteJson
)

$ErrorActionPreference = "Stop"

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

function Get-ExtensionList {
    param([string]$ProfileName, [bool]$UseCurrentProfile, [string]$CodeCli)

    $args = @("--list-extensions", "--show-versions")
    if (-not $UseCurrentProfile) {
        $args = @("--profile", $ProfileName) + $args
    }

    $raw = & $CodeCli @args 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to query VS Code extensions."
    }

    $items = @()
    foreach ($line in $raw) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split "@", 2
        $items += [pscustomobject]@{
            Id      = $parts[0].Trim()
            Version = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }
        }
    }
    return $items | Sort-Object Id -Unique
}

$CodeCli = Get-CodeCli
& $CodeCli --version | Out-Null

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

$Disable = @(
    "github.copilot",
    "github.copilot-chat",
    "vivaxy.vscode-conventional-commits",
    "ms-vscode.powershell-preview",
    "ms-azuretools.vscode-azureappservice",
    "ms-azuretools.vscode-azureresourcegroups",
    "ms-azuretools.vscode-docker",
    "oderwat.indent-rainbow"
)

$Uninstall = @(
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "hookyqr.beautify"
)

$installed = Get-ExtensionList -ProfileName $ProfileName -UseCurrentProfile:$UseCurrentProfile -CodeCli $CodeCli

$rows = foreach ($ext in $installed) {
    $action =
    if ($Keep -contains $ext.Id) { "KEEP" }
    elseif ($Disable -contains $ext.Id) { "DISABLE" }
    elseif ($Uninstall -contains $ext.Id) { "UNINSTALL" }
    else { "REVIEW" }

    [pscustomobject]@{
        Extension = $ext.Id
        Version   = $ext.Version
        Action    = $action
    }
}

$summary = [pscustomobject]@{
    Keep      = ($rows | Where-Object Action -eq "KEEP").Count
    Disable   = ($rows | Where-Object Action -eq "DISABLE").Count
    Uninstall = ($rows | Where-Object Action -eq "UNINSTALL").Count
    Review    = ($rows | Where-Object Action -eq "REVIEW").Count
    Total     = $rows.Count
    Profile   = if ($UseCurrentProfile) { "current-profile" } else { $ProfileName }
}

Write-Host ""
Write-Host "VS Code Extension Audit" -ForegroundColor Cyan
Write-Host "Profile: $($summary.Profile)"
Write-Host "Total:   $($summary.Total)"
Write-Host "Keep:    $($summary.Keep)" -ForegroundColor Green
Write-Host "Disable: $($summary.Disable)" -ForegroundColor Yellow
Write-Host "Remove:  $($summary.Uninstall)" -ForegroundColor Red
Write-Host "Review:  $($summary.Review)" -ForegroundColor Magenta
Write-Host ""

Write-Host "=== KEEP ===" -ForegroundColor Green
$rows | Where-Object Action -eq "KEEP" | Format-Table -AutoSize

Write-Host "=== DISABLE ===" -ForegroundColor Yellow
$rows | Where-Object Action -eq "DISABLE" | Format-Table -AutoSize

Write-Host "=== UNINSTALL ===" -ForegroundColor Red
$rows | Where-Object Action -eq "UNINSTALL" | Format-Table -AutoSize

Write-Host "=== REVIEW ===" -ForegroundColor Magenta
$rows | Where-Object Action -eq "REVIEW" | Format-Table -AutoSize

$outDir = "audit-artifacts\vscode"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$csvPath = Join-Path $outDir "vscode_extension_audit.csv"
$rows | Export-Csv -NoTypeInformation -Path $csvPath

$txtPath = Join-Path $outDir "vscode_extension_audit_summary.txt"
@(
    "VS Code Extension Audit"
    "Profile: $($summary.Profile)"
    "Total: $($summary.Total)"
    "Keep: $($summary.Keep)"
    "Disable: $($summary.Disable)"
    "Uninstall: $($summary.Uninstall)"
    "Review: $($summary.Review)"
) | Set-Content -Path $txtPath

if ($WriteJson) {
    $jsonPath = Join-Path $outDir "vscode_extension_audit.json"
    [pscustomobject]@{
        summary = $summary
        rows    = $rows
    } | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath
}

Write-Host ""
Write-Host "Reports written:"
Write-Host "  $csvPath"
Write-Host "  $txtPath"
if ($WriteJson) {
    Write-Host "  audit-artifacts\vscode\vscode_extension_audit.json"
}
Write-Host ""
Write-Host "Next:"
Write-Host "  Review REVIEW items first."
Write-Host "  Disable before uninstalling."
