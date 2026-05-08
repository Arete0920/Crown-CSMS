#!/usr/bin/env pwsh
<#
.SYNOPSIS
Validates that all gate decision and scorecard JSON outputs conform to required schema
.DESCRIPTION
Ensures JSON structure is correct before gate meeting
Validates all required fields are present
Checks data types match expectations
#>

param(
    [string]$ScorecardPath = "./99_STATUS.json",
    [string]$AuditDecisionPath = "./AUDIT_DECISION.json"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         JSON SCHEMA VALIDATOR - GATE ARTIFACTS            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$allValid = $true
$validationResults = @()

# Validate Scorecard JSON
Write-Host "Validating scorecard: $ScorecardPath" -ForegroundColor Yellow
if (Test-Path $ScorecardPath) {
    try {
        $scorecard = Get-Content $ScorecardPath | ConvertFrom-Json
        
        # Required fields in scorecard
        $requiredFields = @(
            "timestamp",
            "pilot_reference",
            "run_id",
            "technical_runtime",
            "evidence_freeze",
            "automated_minimum_lane_score",
            "governance",
            "compliance",
            "ops",
            "founder",
            "human_minimum_lane_score",
            "gate_decision",
            "gate_ready_for_meeting"
        )
        
        $missingFields = @()
        foreach ($field in $requiredFields) {
            if (-not ($scorecard.PSObject.Properties.Name -contains $field)) {
                $missingFields += $field
            }
        }
        
        if ($missingFields.Count -eq 0) {
            Write-Host "  ✅ All required fields present" -ForegroundColor Green
            $validationResults += "✅ Scorecard: All required fields present"
            
            # Validate field types
            $typeErrors = @()
            
            if (-not ($scorecard.technical_runtime -is [int] -or $scorecard.technical_runtime -is [double])) {
                $typeErrors += "technical_runtime must be numeric"
            }
            if (-not ($scorecard.evidence_freeze -is [int] -or $scorecard.evidence_freeze -is [double])) {
                $typeErrors += "evidence_freeze must be numeric"
            }
            if (-not ($scorecard.gate_ready_for_meeting -is [bool])) {
                $typeErrors += "gate_ready_for_meeting must be boolean"
            }
            
            if ($typeErrors.Count -eq 0) {
                Write-Host "  ✅ All field types correct" -ForegroundColor Green
                $validationResults += "✅ Scorecard: Field types correct"
                
                # Validate value ranges
                $valueErrors = @()
                if ($scorecard.technical_runtime -lt 0 -or $scorecard.technical_runtime -gt 100) {
                    $valueErrors += "technical_runtime out of range (0-100)"
                }
                if ($scorecard.evidence_freeze -lt 0 -or $scorecard.evidence_freeze -gt 100) {
                    $valueErrors += "evidence_freeze out of range (0-100)"
                }
                
                if ($valueErrors.Count -eq 0) {
                    Write-Host "  ✅ All values within valid ranges" -ForegroundColor Green
                    $validationResults += "✅ Scorecard: Values within valid ranges"
                }
                else {
                    Write-Host "  ✗ Value range errors:" -ForegroundColor Red
                    foreach ($err in $valueErrors) {
                        Write-Host "     - $err" -ForegroundColor Red
                    }
                    $validationResults += "✗ Scorecard: Value range errors"
                    $allValid = $false
                }
            }
            else {
                Write-Host "  ✗ Field type errors:" -ForegroundColor Red
                foreach ($err in $typeErrors) {
                    Write-Host "     - $err" -ForegroundColor Red
                }
                $validationResults += "✗ Scorecard: Type errors"
                $allValid = $false
            }
        }
        else {
            Write-Host "  ✗ Missing required fields:" -ForegroundColor Red
            foreach ($field in $missingFields) {
                Write-Host "     - $field" -ForegroundColor Red
            }
            $validationResults += "✗ Scorecard: Missing fields - $($missingFields -join ', ')"
            $allValid = $false
        }
    }
    catch {
        Write-Host "  ✗ JSON parsing error: $($_.Exception.Message)" -ForegroundColor Red
        $validationResults += "✗ Scorecard: JSON parsing error"
        $allValid = $false
    }
}
else {
    Write-Host "  ⚠️  File not found: $ScorecardPath" -ForegroundColor Yellow
    $validationResults += "⚠️ Scorecard: File not found"
}

# Validate Audit Decision JSON (when it exists)
Write-Host ""
Write-Host "Validating audit decision: $AuditDecisionPath" -ForegroundColor Yellow
if (Test-Path $AuditDecisionPath) {
    try {
        $auditDecision = Get-Content $AuditDecisionPath | ConvertFrom-Json
        
        $requiredAuditFields = @(
            "timestamp",
            "pilot_reference",
            "run_id",
            "build_sha",
            "production_tag",
            "decision_authority",
            "compliance_officer",
            "operations_lead",
            "founder",
            "final_decision"
        )
        
        $missingAuditFields = @()
        foreach ($field in $requiredAuditFields) {
            if (-not ($auditDecision.PSObject.Properties.Name -contains $field)) {
                $missingAuditFields += $field
            }
        }
        
        if ($missingAuditFields.Count -eq 0) {
            Write-Host "  ✅ All required fields present" -ForegroundColor Green
            $validationResults += "✅ Audit Decision: All required fields present"
            
            # Validate decision values
            $validDecisions = @("GO", "NO-GO", "PENDING")
            if ($auditDecision.final_decision -notin $validDecisions) {
                Write-Host "  ✗ Invalid final_decision: '$($auditDecision.final_decision)'" -ForegroundColor Red
                $validationResults += "✗ Audit Decision: Invalid final_decision value"
                $allValid = $false
            }
            else {
                Write-Host "  ✅ final_decision value valid" -ForegroundColor Green
                $validationResults += "✅ Audit Decision: final_decision valid"
            }
        }
        else {
            Write-Host "  ⚠️  Missing audit fields (okay if not yet generated): $($missingAuditFields -join ', ')" -ForegroundColor Yellow
            $validationResults += "⚠️ Audit Decision: Incomplete (not yet signed)"
        }
    }
    catch {
        Write-Host "  ✗ JSON parsing error: $($_.Exception.Message)" -ForegroundColor Red
        $validationResults += "✗ Audit Decision: JSON parsing error"
        $allValid = $false
    }
}
else {
    Write-Host "  ℹ️  File not yet created (will be generated at gate meeting)" -ForegroundColor Cyan
    $validationResults += "ℹ️ Audit Decision: Not yet created"
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "VALIDATION RESULTS:" -ForegroundColor Yellow

foreach ($result in $validationResults) {
    Write-Host "  $result" -ForegroundColor $(if($result -like "*✗*") {"Red"} elseif($result -like "*✅*") {"Green"} else {"Yellow"})
}

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($allValid) {
    Write-Host ""
    Write-Host "✅ All JSON artifacts valid and ready for gate meeting" -ForegroundColor Green
    exit 0
}
else {
    Write-Host ""
    Write-Host "❌ JSON validation failed. Fix errors before gate meeting." -ForegroundColor Red
    exit 1
}
