$ErrorActionPreference = "Stop"

$base = "audit-artifacts\release-verify"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$SandboxUrl = if ($env:COMPUWERX_SANDBOX_URL) { $env:COMPUWERX_SANDBOX_URL } else { "" }
$out = "$base\compuwerx_sandbox_capture.txt"

if (-not $SandboxUrl) {
@"
COMPUWERX sandbox URL not provided.
Set COMPUWERX_SANDBOX_URL and rerun.
This artifact is a hard evidence placeholder until sandbox verification is supplied.
"@ | Out-File $out -Encoding utf8
    Write-Host "CompuWerx sandbox URL missing. Wrote placeholder artifact."
    exit 0
}

try {
    $resp = Invoke-WebRequest -Uri $SandboxUrl -Method Get -TimeoutSec 30
@"
URL: $SandboxUrl
Status: $($resp.StatusCode)
Headers:
$($resp.Headers | Out-String)
"@ | Out-File $out -Encoding utf8
} catch {
    $_ | Out-String | Out-File $out -Encoding utf8
}