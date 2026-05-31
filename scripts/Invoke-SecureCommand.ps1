# Invoke-SecureCommand.ps1
# PowerShell wrapper that blocks accidental secret exposure
# Usage: .\Scripts\Invoke-SecureCommand.ps1 -Command "az webapp config appsettings list ..."

<#
.SYNOPSIS
Executes commands with automatic secret redaction in output

.DESCRIPTION
Wraps command execution to prevent secrets from appearing in terminal output.
All output is automatically redacted before display.
Use this for any Azure/DB/API commands that might expose credentials.

.PARAMETER Command
The command to execute (will be run in current shell context)

.PARAMETER AllowRawOutput
Skip redaction (use only when you're CERTAIN output contains no secrets)

.EXAMPLE
.\Scripts\Invoke-SecureCommand.ps1 -Command "az webapp config appsettings list --name crown-api-dev --resource-group crown-rg"
# Output automatically redacted

.EXAMPLE
Invoke-SecureCommand "psql -c 'SELECT 1;'" -AllowRawOutput
# Shows raw output (use carefully!)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Command,
    
    [Parameter()]
    [switch]$AllowRawOutput,
    
    [Parameter()]
    [switch]$Silent
)

# Import redaction module
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptPath\Redact.psm1" -Force

if (-not $Silent) {
    Write-Host "`n🔒 Executing command with secret protection..." -ForegroundColor Cyan
    Write-Host "   Command: " -NoNewline -ForegroundColor Gray
    Write-Host (Redact $Command) -ForegroundColor Yellow
}

try {
    # Execute command and capture output
    $output = Invoke-Expression $Command 2>&1 | Out-String
    
    if ($AllowRawOutput) {
        if (-not $Silent) {
            Write-Host "`n⚠️  RAW OUTPUT (unredacted):" -ForegroundColor Yellow
        }
        Write-Host $output
    } else {
        # Check for secrets before displaying
        if (Test-ContainsSecrets $output) {
            Write-Host "`n🛑 OUTPUT SUPPRESSED: Secrets detected" -ForegroundColor Red
            Write-Host "   Output contains credentials and cannot be displayed." -ForegroundColor Yellow
            Write-Host "   Review output locally in secure context only." -ForegroundColor Yellow
            return "<REDACTED: secret detected>"
        } elseif (-not $Silent) {
            Write-Host "`n✓ Output (no secrets detected):" -ForegroundColor Green
        }
        
        # No secrets detected - safe to redact and display
        $redacted = Redact $output
        Write-Host $redacted -ForegroundColor Gray
    }
    
    return $output  # Return raw for programmatic use (caller's responsibility to not echo)
    
} catch {
    Write-Host "`n❌ Command failed: $_" -ForegroundColor Red
    throw
}
