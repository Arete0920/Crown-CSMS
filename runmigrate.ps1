# Crown2026 - Migrate DB
Set-Location "$PSScriptRoot\backend"

$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTHONUNBUFFERED="1"

.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate
