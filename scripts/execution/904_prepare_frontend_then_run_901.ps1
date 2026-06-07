param(
    [switch]$SkipNpmCi,
    [switch]$SkipHeavyGates
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Has-FrontendTool {
    param([string]$FrontendDir, [string]$ToolName)
    $binDir = Join-Path $FrontendDir "node_modules\.bin"
    return ((Test-Path (Join-Path $binDir "$ToolName.cmd")) -or (Test-Path (Join-Path $binDir $ToolName)))
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

Require-Command git
Require-Command npm

$frontendDir = Join-Path $repoRoot "frontend\dashboards"
if (-not (Test-Path (Join-Path $frontendDir "package-lock.json"))) {
    throw "Missing frontend/dashboards/package-lock.json. Cannot prepare deterministic frontend dependencies."
}

$hasVitest = Has-FrontendTool -FrontendDir $frontendDir -ToolName "vitest"
$hasVite = Has-FrontendTool -FrontendDir $frontendDir -ToolName "vite"

if ((-not $hasVitest -or -not $hasVite) -and $SkipNpmCi) {
    throw "Frontend dependencies are missing but -SkipNpmCi was used. Run without -SkipNpmCi or run npm ci in frontend/dashboards first."
}

if (-not $hasVitest -or -not $hasVite) {
    Write-Host "Frontend node_modules tools are missing. Running npm ci in frontend/dashboards."
    Push-Location $frontendDir
    try {
        npm ci
    } finally {
        Pop-Location
    }
}

$hasVitest = Has-FrontendTool -FrontendDir $frontendDir -ToolName "vitest"
$hasVite = Has-FrontendTool -FrontendDir $frontendDir -ToolName "vite"

if (-not $hasVitest -or -not $hasVite) {
    throw "Frontend dependency preparation failed. Missing vitest=$(-not $hasVitest), vite=$(-not $hasVite)."
}

$env:VITE_SANDBOX_READY_ONLY = "true"
$env:VITE_HIDE_UNREADY_NAV = "true"
$env:VITE_SANDBOX_MODE = "1"
$env:CROWN_ENV = "production"
$env:CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = "0"
$env:TENANT_HEADER_REQUIRED = "0"

$args901 = @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\execution\901_executive_sandbox_gate.ps1", "-SkipInstall")
if ($SkipHeavyGates) {
    $args901 += "-SkipHeavyGates"
}

Write-Host "Running 901 after frontend dependency preparation."
powershell @args901
exit $LASTEXITCODE
