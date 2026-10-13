$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$scriptPath = Join-Path $sourceRoot 'scripts\execution\81_phase34_archive_and_purge_enforcement.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'Archive PowerShell syntax failed.' }
$phase = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-Phase3'
}, $true)
if (-not $phase) { throw 'Archive entry point was not found.' }
# Load only the function definition, never the script's orchestration/purge code.
. ([scriptblock]::Create($phase.Extent.Text))
function New-ArtifactRoot {
    param($AuditRoot, $Slug)
    New-Item -ItemType Directory -Path $AuditRoot -Force | Out-Null
    return $AuditRoot
}
$fixture = Join-Path $env:TEMP ('crown-archive-fixture-' + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path (Join-Path $fixture 'tools') -Force | Out-Null
    Copy-Item (Join-Path $sourceRoot 'tools\create_verified_git_bundle.py') (Join-Path $fixture 'tools')
    Copy-Item (Join-Path $sourceRoot 'tools\verify_remediated_git_bundle.sh') (Join-Path $fixture 'tools')
    git -C $fixture init -q
    git -C $fixture config user.name 'Archive Fixture'
    git -C $fixture config user.email 'fixture@example.invalid'
    $relative = 'solomon_governance_c1/governance/c1/runtime/audit_pack/20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem'
    $forbidden = Join-Path $fixture $relative
    New-Item -ItemType Directory -Path (Split-Path $forbidden) -Force | Out-Null
    Set-Content -LiteralPath $forbidden -Value 'ordinary fixture text; no private material'
    git -C $fixture add .
    git -C $fixture commit -qm 'fixture historical path'
    git -C $fixture rm -q -- $relative
    git -C $fixture commit -qm 'fixture current-tree removal'
    if ($LASTEXITCODE -ne 0) { throw 'Fixture Git preparation failed.' }
    $paths = [pscustomobject]@{ Root = $fixture; AuditRoot = Join-Path $fixture 'audit-output' }
    Push-Location $fixture
    try {
        $blocked = $false
        try { Invoke-Phase3 -Paths $paths -PhaseState ([pscustomobject]@{Phase2Ready = $true}) -GateRows @() }
        catch {
            if ($_.Exception.Message -ne 'History-verified archive creation failed.') { throw }
            $blocked = $true
        }
        if (-not $blocked) { throw 'Exposed history was not rejected by the archive entry point.' }
        if (Test-Path (Join-Path $paths.AuditRoot 'repo.bundle')) { throw 'Rejected archive was published.' }
    }
    finally { Pop-Location }
    Write-Host 'Windows archive entry point rejected removed-but-reachable history before publication.'
}
finally { Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue }
# The rejected native command leaves LASTEXITCODE=1; the asserted rejection is success.
exit 0
