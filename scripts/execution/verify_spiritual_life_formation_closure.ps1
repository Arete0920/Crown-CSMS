$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string]$LogPath,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    "=== $Label ===" | Out-File $LogPath -Encoding UTF8
    & $Command 2>&1 | Tee-Object -FilePath $LogPath -Append

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE. See $LogPath"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$base = "docs\proof\spiritual-life-formation-closure"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== REPO ===" | Out-File "$base\00_repo.txt" -Encoding UTF8
git status -sb | Add-Content "$base\00_repo.txt"
git branch --show-current | Add-Content "$base\00_repo.txt"
git rev-parse HEAD | Add-Content "$base\00_repo.txt"

"=== MODEL REGISTRATION SCAN ===" | Out-File "$base\01_model_registration_scan.txt" -Encoding UTF8
$registrationPattern = "formation_models|PortraitDomain|BiblicalWorldviewPriority|FormationCampaign|FormationArtifact|DevotionalContent|BiblicalIntegrationRecord|SpiritualDomainRating"
Select-String -Path "backend\spiritual_life\models.py" -Pattern $registrationPattern | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\01_model_registration_scan.txt"

$classPattern = "class PortraitDomain|class BiblicalWorldviewPriority|class FormationCampaign|class FormationArtifact|class DevotionalContent|class BiblicalIntegrationRecord|class SpiritualDomainRating"
Select-String -Path "backend\spiritual_life\formation_models.py" -Pattern $classPattern | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\01_model_registration_scan.txt"

"=== EXISTING MIGRATION SCAN BEFORE ===" | Out-File "$base\02_existing_migration_scan_before.txt" -Encoding UTF8
Get-ChildItem "backend\spiritual_life\migrations" -Filter "*.py" | Select-Object Name | Format-Table -AutoSize | Out-String | Add-Content "$base\02_existing_migration_scan_before.txt"
Select-String -Path "backend\spiritual_life\migrations\*.py" -Pattern $registrationPattern | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\02_existing_migration_scan_before.txt"

Invoke-Checked -Label "DJANGO CHECK BEFORE" -LogPath "$base\03_django_check_before.txt" -Command { python backend\manage.py check }
Invoke-Checked -Label "GENERATE SPIRITUAL LIFE MIGRATION" -LogPath "$base\04_makemigrations_spiritual_life.txt" -Command { python backend\manage.py makemigrations spiritual_life }

"=== MIGRATION SCAN AFTER ===" | Out-File "$base\05_migration_scan_after.txt" -Encoding UTF8
Get-ChildItem "backend\spiritual_life\migrations" -Filter "*.py" | Select-Object Name | Format-Table -AutoSize | Out-String | Add-Content "$base\05_migration_scan_after.txt"
Select-String -Path "backend\spiritual_life\migrations\*.py" -Pattern $registrationPattern | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\05_migration_scan_after.txt"

Invoke-Checked -Label "MIGRATION DRY RUN" -LogPath "$base\06_migration_check.txt" -Command { python backend\manage.py makemigrations --check --dry-run }
Invoke-Checked -Label "MIGRATE PLAN" -LogPath "$base\07_migrate_plan.txt" -Command { python backend\manage.py migrate --plan }
Invoke-Checked -Label "SPIRITUAL LIFE TESTS" -LogPath "$base\08_spiritual_life_tests.txt" -Command { pytest backend\spiritual_life -q }

"=== FINAL STATUS ===" | Out-File "$base\09_final_status.txt" -Encoding UTF8
git status -sb | Add-Content "$base\09_final_status.txt"
git diff --stat | Add-Content "$base\09_final_status.txt"
git diff -- backend\spiritual_life\migrations | Add-Content "$base\09_final_status.txt"

Write-Host "PASS: Spiritual Life formation closure proof generated at $base"
