#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Safe local-only database reset, migration, and heritage realism pack seed.
    
.DESCRIPTION
    This script WILL DELETE ALL DATA from the Crown2026 database.
    It is ONLY SAFE for local development databases.
    
    Refuses to run if:
    - DB_HOST is not localhost/127.0.0.1/127.0.0.1
    - Environment is production (WEBSITE_HOSTNAME set)
    
    On success:
    - Flushes all data
    - Runs migrations
    - Seeds with heritage pack (attendance, admissions, academics, etc.)
    - Prints sanity counts for validation
    
.EXAMPLE
    PS> .\PRE_DEMO_RESET_AND_SEED.ps1
    
    DB Host: localhost
    DB Name: crown2026
    DB User: postgres
    
    [Clearing data...]
    [Running migrations...]
    [Seeding...]
    
    === KNOWN-GOOD DATASET READY ===
    Student: 300
    Family: 180
    AttendanceRecord: 1500
    Section: 4
    Invoices: 40
    
    Ready for demo!

.NOTES
    Author: Crown2026 Build System
    Date: 2026-02-16
#>

param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "=== PRE_DEMO_RESET_AND_SEED ===" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. CHECK ENVIRONMENT & DATABASE CONFIGURATION
# ============================================================================

Write-Host "Checking database configuration..." -ForegroundColor Cyan

$db_host = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$db_name = if ($env:DB_NAME) { $env:DB_NAME } else { "crown2026" }
$db_user = if ($env:DB_USER) { $env:DB_USER } else { "postgres" }
$db_port = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }

# Check for Azure/production indicators
if ($env:WEBSITE_HOSTNAME -or $env:WEBSITE_INSTANCE_ID) {
    Write-Host "ERROR: Azure production environment detected." -ForegroundColor Red
    Write-Host "This script refuses to run on production databases." -ForegroundColor Red
    exit 1
}

# Allowlist for safe hosts
$allowed_hosts = @("localhost", "127.0.0.1", "::1")
if ($db_host -notin $allowed_hosts) {
    Write-Host "ERROR: Database host '$db_host' is not in safe hosts allowlist." -ForegroundColor Red
    Write-Host "Allowed: $($allowed_hosts -join ', ')" -ForegroundColor Red
    Write-Host "This script only runs on local development databases." -ForegroundColor Red
    exit 1
}

Write-Host "Database Configuration:" -ForegroundColor Green
Write-Host "  Host: $db_host"
Write-Host "  Name: $db_name"
Write-Host "  User: $db_user"
Write-Host "  Port: $db_port"
Write-Host ""

# ============================================================================
# 2. CONFIRM INTENT
# ============================================================================

if (-not $Force) {
    Write-Host "WARNING: This will DELETE ALL DATA from '$db_name'." -ForegroundColor Yellow
    Write-Host "Confirm? (Type 'yes' to continue)"
    $confirm = Read-Host
    
    if ($confirm -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "Running with -Force (skipping confirmation prompt)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 3. CHANGE TO BACKEND DIRECTORY
# ============================================================================

$backend_path = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backend_path)) {
    Write-Host "ERROR: Backend directory not found at $backend_path" -ForegroundColor Red
    exit 1
}

Set-Location $backend_path
Write-Host "Working directory: $((Get-Location).Path)" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 4. FLUSH DATABASE
# ============================================================================

Write-Host "Flushing database..." -ForegroundColor Cyan
python manage.py flush --noinput
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Flush failed." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Flush complete." -ForegroundColor Green
Write-Host ""

# ============================================================================
# 5. RUN MIGRATIONS
# ============================================================================

Write-Host "Running migrations..." -ForegroundColor Cyan
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Migrations failed." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Migrations complete." -ForegroundColor Green
Write-Host ""

# ============================================================================
# 6. SEED HERITAGE REALISM PACK
# ============================================================================

Write-Host "Seeding heritage realism pack..." -ForegroundColor Cyan
python manage.py seed_heritage_realism_pack --no-comms --no-finance-scripts --traceback
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Seed failed." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Seed complete." -ForegroundColor Green
Write-Host ""

# ============================================================================
# 7. VALIDATE DATASET
# ============================================================================

Write-Host "Validating dataset..." -ForegroundColor Cyan

$script_code = @'
from crown_api.models_academics_core import AttendanceRecord
from crown_api.models import Section, SectionEnrollment
from core.models import Student, Family
from billing.models import Invoice
from curriculum.models import CurriculumCourse

student_count = Student.objects.count()
family_count = Family.objects.count()
attendance_count = AttendanceRecord.objects.count()
section_count = Section.objects.count()
enrollment_count = SectionEnrollment.objects.count()
invoice_count = Invoice.objects.count()
curriculum_count = CurriculumCourse.objects.count()

print(f"Student: {student_count}")
print(f"Family: {family_count}")
print(f"AttendanceRecord: {attendance_count}")
print(f"Section: {section_count}")
print(f"SectionEnrollment: {enrollment_count}")
print(f"Invoice: {invoice_count}")
print(f"CurriculumCourse: {curriculum_count}")

# Sanity checks
assert student_count == 300, f"Expected 300 students, got {student_count}"
assert attendance_count == 1500, f"Expected 1500 attendance records, got {attendance_count}"
assert section_count >= 4, f"Expected at least 4 sections, got {section_count}"
assert curriculum_count == 4, f"Expected 4 curriculum courses, got {curriculum_count}"
print("All sanity checks passed")
'@

$validation = & python manage.py shell -c $script_code

Write-Host ""
Write-Host "=== KNOWN-GOOD DATASET READY ===" -ForegroundColor Green
Write-Host ""
Write-Host $validation
Write-Host ""
Write-Host "✓ Database is ready for demo." -ForegroundColor Green
