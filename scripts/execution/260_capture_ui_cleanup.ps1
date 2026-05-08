param(
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
$CaptureRoot = "audit-artifacts\ui-cleanup-captures\$Stamp"
New-Item -ItemType Directory -Force -Path $CaptureRoot, (Join-Path $CaptureRoot "screenshots") | Out-Null

$Packet = Join-Path $Room "DEV4_UI_POLISH_PACKET.md"
$Evidence = Join-Path $Room "20_UI_DASHBOARD_ROUTE_EVIDENCE.csv"
$Board = Join-Path $Room "30_UI_CLEANUP_BOARD.csv"

Copy-Item $Evidence (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) -Force
Copy-Item $Board (Join-Path $CaptureRoot (Split-Path $Board -Leaf)) -Force

@"
# UI Cleanup Capture Workspace

- Control room: $Room
- Capture root: $CaptureRoot
- Packet: $Packet
- Evidence seed: $(Join-Path $CaptureRoot (Split-Path $Evidence -Leaf))
- Cleanup board seed: $(Join-Path $CaptureRoot (Split-Path $Board -Leaf))

Use this folder for before and after screenshots plus route-level proof.
"@ | Set-Content (Join-Path $CaptureRoot "README.md") -Encoding UTF8

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    & $codeCmd.Source --reuse-window $Packet | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Evidence -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot (Split-Path $Board -Leaf)) | Out-Null
    & $codeCmd.Source --reuse-window (Join-Path $CaptureRoot "README.md") | Out-Null
}

Write-Host "UI cleanup capture workspace ready: $CaptureRoot"
