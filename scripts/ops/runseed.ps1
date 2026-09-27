# CROWN - Seed demo data
Set-Location "$PSScriptRoot\backend"

$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONUNBUFFERED="1"

.\venv\Scripts\python.exe manage.py seed_demo_school --wipe --students 300 --tuition 12000 --aid_pct 35
