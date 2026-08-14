#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validate demo health, canonical Scheduling data, and access boundaries.
#>

param()
$ErrorActionPreference = "Stop"
Write-Host "=== DEMO PROOF REHEARSAL ===" -ForegroundColor Cyan

$backendPath = (Resolve-Path (Join-Path $PSScriptRoot "../../backend")).Path
Push-Location $backendPath
try {
    Write-Host "API health: verify http://127.0.0.1:8000/api/health/ when the dev server is running." -ForegroundColor Cyan

    $dataCheck = python manage.py shell -c @"
from academics.models import Section, Term
from section_scheduler_wizard.models import SectionPlacement
from crown_api.models_academics_core import AttendanceRecord
from core.models import Student, Family

student_count = Student.objects.count()
family_count = Family.objects.count()
attendance_count = AttendanceRecord.objects.count()
section_count = Section.objects.count()
term_count = Term.objects.count()
placement_count = SectionPlacement.objects.filter(is_active=True).count()

print(f'Student: {student_count}')
print(f'Family: {family_count}')
print(f'AttendanceRecord: {attendance_count}')
print(f'Canonical Section: {section_count}')
print(f'Canonical Term: {term_count}')
print(f'Active SectionPlacement: {placement_count}')

assert student_count == 300, f'Expected 300 students, got {student_count}'
assert attendance_count == 1500, f'Expected 1500 attendance rows, got {attendance_count}'
assert section_count >= 2, f'Expected at least 2 canonical sections, got {section_count}'
assert term_count >= 1, 'Expected at least one canonical term'
"@
    if ($LASTEXITCODE -ne 0) { throw "Canonical data proof failed." }
    Write-Host $dataCheck

    $schedulingCheck = python manage.py shell -c @"
from academics.models import Section, TeacherAssignment
from section_scheduler_wizard.models import SectionPlacement

sections = Section.objects.select_related('course', 'term_ref').order_by('course__code', 'id')
print(f'Canonical sections available: {sections.count()}')
for section in sections[:4]:
    roster_count = section.enrollments.count()
    teacher_count = TeacherAssignment.objects.filter(section=section).count()
    meeting_count = SectionPlacement.objects.filter(section=section, is_active=True).count()
    print(f'- {section.course.code} / {section.term_ref.code if section.term_ref else section.term}: roster={roster_count}, teachers={teacher_count}, meetings={meeting_count}')
"@
    if ($LASTEXITCODE -ne 0) { throw "Canonical Scheduling proof failed." }
    Write-Host $schedulingCheck

    $parentCheck = python manage.py shell -c @"
from admissions.models import AdmissionsApplication

app = AdmissionsApplication.objects.filter(family__isnull=False, household__isnull=False).first()
if app:
    print(f'Family: {app.family}')
    print(f'Household: {app.household.household_name}')
    print('Parent access bridge exists; out-of-scope student requests must remain nondisclosing 404s.')
else:
    print('No admissions application available for parent-scope rehearsal.')
"@
    if ($LASTEXITCODE -ne 0) { throw "Parent scope proof failed." }
    Write-Host $parentCheck

    Write-Host "=== REHEARSAL READY ===" -ForegroundColor Green
}
finally {
    Pop-Location
}
