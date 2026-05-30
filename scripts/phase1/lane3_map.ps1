param(
  [string]$OutFile = "$PSScriptRoot\..\..\LANE3_ATTENDANCE_MAP.txt"
)

$ErrorActionPreference="Stop"

function WriteSection($title) {
  "`n===== $title =====`n" | Out-File -FilePath $OutFile -Append -Encoding UTF8
}

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backend = Join-Path $repo "backend"
$py = Join-Path $repo ".venv\Scripts\python.exe"

if (!(Test-Path $backend)) { throw "backend/ not found at: $backend" }
if (!(Test-Path $py)) { throw "python not found at: $py" }

Remove-Item -Force -ErrorAction SilentlyContinue $OutFile

"LANE3_ATTENDANCE_MAP=BEGIN" | Out-File -FilePath $OutFile -Encoding UTF8
"Generated: $(Get-Date -Format s)" | Out-File -FilePath $OutFile -Append -Encoding UTF8

WriteSection "1) URL Inventory (attendance / section / parent read)"
Push-Location $backend
try {
  & $py manage.py show_urls 2>$null | Select-String -Pattern "attendance|absent|tardy|present|section|roster|parent" -CaseSensitive:$false |
    ForEach-Object { $_.Line } |
    Out-File -FilePath $OutFile -Append -Encoding UTF8
} finally {
  Pop-Location
}

WriteSection "2) Frontend Route Inventory (attendance)"
$router = Join-Path $repo "frontend\dashboards\src\routes\router.jsx"
if (Test-Path $router) {
  Select-String -Path $router -Pattern "Attendance|attendance" -CaseSensitive:$false |
    ForEach-Object { $_.Line } |
    Out-File -FilePath $OutFile -Append -Encoding UTF8
} else {
  "router.jsx not found at expected path: $router" | Out-File -FilePath $OutFile -Append -Encoding UTF8
}

WriteSection "3) Model Inventory Probe (best effort; prints likely section/student/attendance models)"
Push-Location $backend
try {
  & $py manage.py shell -c "
from django.apps import apps
targets=[]
for m in apps.get_models():
    n=(m.__module__+'.'+m.__name__).lower()
    if any(k in n for k in ['attendance','section','roster','student','enrollment','parent','household']):
        targets.append(m)
print('MODEL_COUNT', len(targets))
for m in targets[:80]:
    try:
        obj = m.objects.first()
        oid = getattr(obj,'id',None) if obj else None
        print(m.__module__+'.'+m.__name__, 'FIRST_ID=', oid)
    except Exception as e:
        print(m.__module__+'.'+m.__name__, 'ERR', e)
" 2>&1 | Out-File -FilePath $OutFile -Append -Encoding UTF8
} finally {
  Pop-Location
}

"`nLANE3_ATTENDANCE_MAP=DONE" | Out-File -FilePath $OutFile -Append -Encoding UTF8
Write-Host "DONE: $OutFile" -ForegroundColor Green
