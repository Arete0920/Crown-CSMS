#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Safe local-only database reset, migration, Heritage seed, and canonical Scheduling seed.
#>

param([switch]$Force)

$ErrorActionPreference = "Stop"
Write-Host "=== PRE_DEMO_RESET_AND_SEED ===" -ForegroundColor Cyan

$dbHost = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$dbName = if ($env:DB_NAME) { $env:DB_NAME } else { "crown2026" }
$allowedHosts = @("localhost", "127.0.0.1", "::1")

if ($env:WEBSITE_HOSTNAME -or $env:WEBSITE_INSTANCE_ID) {
    throw "Refusing to run demo reset in Azure/production."
}
if ($dbHost -notin $allowedHosts) {
    throw "Database host '$dbHost' is not local."
}
if (-not $Force) {
    $confirm = Read-Host "This will DELETE ALL DATA from '$dbName'. Type 'yes' to continue"
    if ($confirm -ne "yes") {
        Write-Host "Cancelled."
        exit 0
    }
}

$backendPath = (Resolve-Path (Join-Path $PSScriptRoot "../../backend")).Path
Push-Location $backendPath
try {
    Write-Host "Flushing local database..." -ForegroundColor Cyan
    python manage.py flush --noinput
    if ($LASTEXITCODE -ne 0) { throw "Flush failed." }

    Write-Host "Running migrations..." -ForegroundColor Cyan
    python manage.py migrate
    if ($LASTEXITCODE -ne 0) { throw "Migrations failed." }

    Write-Host "Seeding Heritage realism pack..." -ForegroundColor Cyan
    python manage.py seed_heritage_realism_pack --no-comms --no-finance-scripts --traceback
    if ($LASTEXITCODE -ne 0) { throw "Heritage seed failed." }

    Write-Host "Seeding canonical Scheduling masters..." -ForegroundColor Cyan
    python scripts/seed_scheduling.py
    if ($LASTEXITCODE -ne 0) { throw "Canonical Scheduling seed failed." }

    Write-Host "Replaying canonical Scheduling seed to prove idempotency..." -ForegroundColor Cyan
    python scripts/seed_scheduling.py
    if ($LASTEXITCODE -ne 0) { throw "Canonical Scheduling seed replay failed." }

    $scriptCode = @'
from academics.models import Section, Term
from core.models import AcademicYear, Student, Family
from billing.models import Invoice
from curriculum.models import CurriculumCourse
from crown_api.models_academics_core import AttendanceRecord

student_count = Student.objects.count()
family_count = Family.objects.count()
attendance_count = AttendanceRecord.objects.count()
section_count = Section.objects.count()
term_count = Term.objects.count()
invoice_count = Invoice.objects.count()
curriculum_count = CurriculumCourse.objects.count()

print(f"Student: {student_count}")
print(f"Family: {family_count}")
print(f"AttendanceRecord: {attendance_count}")
print(f"Canonical Section: {section_count}")
print(f"Canonical Term: {term_count}")
print(f"Invoice: {invoice_count}")
print(f"CurriculumCourse: {curriculum_count}")

assert student_count == 300, f"Expected 300 students, got {student_count}"
assert attendance_count == 1500, f"Expected 1500 attendance records, got {attendance_count}"
assert section_count >= 4, f"Expected at least 4 canonical sections, got {section_count}"
assert term_count >= 1, "Expected at least one canonical term"
assert curriculum_count == 4, f"Expected 4 curriculum courses, got {curriculum_count}"

current_years = AcademicYear.objects.filter(is_current=True).order_by("school_id", "start_date")
assert current_years.exists(), "Expected at least one current academic year"
for year in current_years:
    year_terms = Term.objects.filter(school_id=year.school_id, academic_year=year)
    assert year_terms.exists(), f"Expected canonical term for current academic year {year.id}"
    for term in year_terms:
        assert term.start_date >= year.start_date, (
            f"Term {term.code} starts before academic year {year.id}: "
            f"{term.start_date} < {year.start_date}"
        )
        assert term.end_date <= year.end_date, (
            f"Term {term.code} ends after academic year {year.id}: "
            f"{term.end_date} > {year.end_date}"
        )

invalid_sections = Section.objects.filter(term_ref__isnull=True).count()
assert invalid_sections == 0, f"Expected every canonical section to reference a canonical term; found {invalid_sections}"
print("All sanity and Scheduling authority checks passed")
'@

    python manage.py shell -c $scriptCode
    if ($LASTEXITCODE -ne 0) { throw "Dataset validation failed." }

    Write-Host "=== KNOWN-GOOD DATASET READY ===" -ForegroundColor Green
}
finally {
    Pop-Location
}
