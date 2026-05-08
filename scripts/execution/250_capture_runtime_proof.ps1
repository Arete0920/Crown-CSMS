param(
    [ValidateSet("Tenant", "RBAC", "Workflow")]
    [string]$Lane = "Tenant",
    [string]$ControlRoomPath = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Set-Location (git rev-parse --show-toplevel)

function Resolve-LatestControlRoom {
    if ($ControlRoomPath -and (Test-Path $ControlRoomPath)) {
        return (Resolve-Path $ControlRoomPath).Path
    }

    $base = "audit-artifacts\execution-control-room"
    $latest = Get-ChildItem $base -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No execution control room output found. Run 271_execution_control_room_pack.ps1 first."
    }

    return $latest.FullName
}

$Room = Resolve-LatestControlRoom
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CaptureRoot = "audit-artifacts\runtime-proof-captures\$Stamp\$Lane"
New-Item -ItemType Directory -Force -Path $CaptureRoot, (Join-Path $CaptureRoot "api"), (Join-Path $CaptureRoot "browser"), (Join-Path $CaptureRoot "screenshots") | Out-Null

switch ($Lane) {
    "Tenant" {
        $Packet = Join-Path $Room "DEV125_TENANT_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "10_TENANT_RUNTIME_EVIDENCE.csv"
    }
    "RBAC" {
        $Packet = Join-Path $Room "DEV15_RBAC_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "11_RBAC_RUNTIME_EVIDENCE.csv"
    }
    "Workflow" {
        $Packet = Join-Path $Room "DEV23_WORKFLOW_RUNTIME_PACKET.md"
        $Evidence = Join-Path $Room "12_WORKFLOW_RUNTIME_EVIDENCE.csv"
    }
}

Copy-Item $Evidence (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) -Force

@"
# Runtime Proof Capture Workspace

- Lane: $Lane
- Control room: $Room
- Capture root: $CaptureRoot
- Packet: $Packet
- Evidence seed: $(Join-Path $CaptureRoot (Split-Path $Evidence -Leaf))

Use this folder for screenshots, browser captures, and command output tied to the evidence CSV.
"@ | Set-Content (Join-Path $CaptureRoot "README.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window $Packet | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot "README.md") | Out-Null
}

Write-Host "Runtime proof capture workspace ready: $CaptureRoot"
