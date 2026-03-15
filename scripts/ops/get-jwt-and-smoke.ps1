param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$Username,

    [Parameter(Mandatory = $true)]
    [string]$Password
)

$ErrorActionPreference = "Stop"

$OutputDir = "_warroom"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$loginUrl = "$BaseUrl/api/auth/login/"
$body = @{
    username = $Username
    password = $Password
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri $loginUrl -Method POST -ContentType "application/json" -Body $body -SkipHttpErrorCheck

@(
    "LOGIN URL: $loginUrl"
    "STATUS: $([int]$response.StatusCode)"
    "BODY:"
    $response.Content
) | Set-Content -Path "$OutputDir/dev_login_result.txt" -Encoding UTF8

try {
    $json = $response.Content | ConvertFrom-Json
    $token = $json.access
    if (-not $token) {
        throw "No access token found in login response."
    }
    $token | Set-Content -Path "$OutputDir/dev_jwt.txt" -Encoding UTF8
    Write-Host "JWT written to $OutputDir/dev_jwt.txt"
}
catch {
    Write-Error "Login succeeded or returned content, but token extraction failed. Check _warroom/dev_login_result.txt"
    exit 1
}
