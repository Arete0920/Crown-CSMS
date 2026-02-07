# Redact.psm1
# PowerShell module for automatic secret redaction
# Usage: Import-Module .\Scripts\Redact.psm1

function Redact {
    <#
    .SYNOPSIS
    Redacts secrets from strings before display or logging
    
    .DESCRIPTION
    Removes passwords, tokens, secrets, keys, and connection strings from text.
    Use this before Write-Host, logging, or pasting to chat.
    
    .PARAMETER Text
    The string to redact
    
    .EXAMPLE
    Redact "DB_PASSWORD=example_password_123"
    # Returns: DB_PASSWORD=<REDACTED>
    
    .EXAMPLE
    Get-Content .\output.txt | Redact
    # Redacts entire file content
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [AllowEmptyString()]
        [string]$Text
    )
    
    process {
        if (-not $Text) { return $Text }
        
        $result = $Text
        
        # 1) Generic secret patterns (case-insensitive)
        $result = $result -replace '(?i)(password|pwd|secret|token|key|apikey|api_key)\s*[:=]\s*["'']?[^"''\s]+', '$1=<REDACTED>'
        
        # 2) Postgres connection strings
        $result = $result -replace '(?i)postgres(?:ql)?://([^:]+):([^@]+)(@)', 'postgres://$1:<REDACTED>$3'
        
        # 3) Bearer tokens (JWT-like)
        $result = $result -replace '(?i)Bearer\s+[A-Za-z0-9_\-\.]{20,}', 'Bearer <REDACTED>'
        
        # 4) Crown-specific patterns
        $result = $result -replace 'CrownPG\d{4}[A-Za-z0-9!@#$%^&*()_+=-]+', '<REDACTED>'
        $result = $result -replace 'DevOpsSecret_Crown\d{4}_[A-Za-z0-9_]+', '<REDACTED>'
        $result = $result -replace 'CrownCi[A-Za-z0-9!@#$%^&*()]+', '<REDACTED>'
        
        # 5) Generic passwords (8+ chars with special chars)
        $result = $result -replace '(?i)password\s*[:=]\s*["'']?[A-Za-z0-9!@#$%^&*()_+=-]{8,}["'']?', 'password=<REDACTED>'
        
        return $result
    }
}

function Write-SafeHost {
    <#
    .SYNOPSIS
    Drop-in replacement for Write-Host that auto-redacts secrets
    
    .DESCRIPTION
    Checks for secrets and suppresses output entirely if detected.
    Use this instead of Write-Host for any output that might contain secrets.
    
    .PARAMETER SuppressIfSecrets
    If $true (default), completely suppresses output when secrets detected.
    If $false, redacts but still displays (less safe).
    
    .EXAMPLE
    Write-SafeHost "Password: example_password_123"
    # Displays: <REDACTED: secret detected>
    #>
    [CmdletBinding()]
    param(
        [Parameter(Position=0, ValueFromPipeline=$true)]
        [string]$Object,
        
        [Parameter()]
        [ConsoleColor]$ForegroundColor,
        
        [Parameter()]
        [ConsoleColor]$BackgroundColor,
        
        [Parameter()]
        [switch]$SuppressIfSecrets = $true
    )
    
    process {
        # Check for secrets first
        if ($SuppressIfSecrets -and (Test-ContainsSecrets $Object)) {
            $params = @{}
            if ($ForegroundColor) { $params['ForegroundColor'] = $ForegroundColor }
            if ($BackgroundColor) { $params['BackgroundColor'] = $BackgroundColor }
            
            Write-Host "<REDACTED: secret detected>" @params
            return
        }
        
        # No secrets detected or suppression disabled - redact and display
        $redacted = Redact $Object
        
        $params = @{}
        if ($ForegroundColor) { $params['ForegroundColor'] = $ForegroundColor }
        if ($BackgroundColor) { $params['BackgroundColor'] = $BackgroundColor }
        
        Write-Host $redacted @params
    }
}

function Copy-SafeClipboard {
    <#
    .SYNOPSIS
    Copies text to clipboard with automatic redaction
    
    .DESCRIPTION
    Redacts secrets before copying to clipboard.
    Use this before pasting anything to chat/external tools.
    
    .EXAMPLE
    Get-Content .\log.txt | Copy-SafeClipboard
    # Clipboard contains redacted version
    #>
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true)]
        [string]$InputObject
    )
    
    begin {
        $lines = @()
    }
    
    process {
        $lines += (Redact $InputObject)
    }
    
    end {
        $lines -join "`n" | Set-Clipboard
        Write-Host "✓ Copied to clipboard (secrets redacted)" -ForegroundColor Green
    }
}

function Test-ContainsSecrets {
    <#
    .SYNOPSIS
    Checks if text contains potential secrets
    
    .DESCRIPTION
    Returns $true if text matches secret patterns, $false otherwise.
    Use this as a safety check before displaying or logging.
    
    .EXAMPLE
    if (Test-ContainsSecrets "password=Crown2026!") {
        Write-Host "WARNING: Contains secrets!"
    }
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Text
    )
    
    $patterns = @(
        '(?i)(password|pwd|secret|token|key)\s*[:=]\s*["'']?[^"''\s]+',
        'postgres(?:ql)?://[^:]+:([^@]+)@',
        'Bearer\s+[A-Za-z0-9_\-\.]{20,}',
        'CrownPG\d{4}',
        'DevOpsSecret_Crown',
        'CrownCi[A-Za-z0-9]+'
    )
    
    foreach ($pattern in $patterns) {
        if ($Text -match $pattern) {
            return $true
        }
    }
    
    return $false
}

# Export functions
Export-ModuleMember -Function Redact, Write-SafeHost, Copy-SafeClipboard, Test-ContainsSecrets
