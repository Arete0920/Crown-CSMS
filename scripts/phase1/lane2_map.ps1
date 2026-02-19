$ErrorActionPreference="Stop"
Set-StrictMode -Version Latest

Write-Host "== LANE 2 MAP: URL PATTERNS ==" -ForegroundColor Cyan

$env:CROWN_DEMO_MODE="true"
$env:DJANGO_SETTINGS_MODULE="crown_api.settings"

& "$env:USERPROFILE\OneDrive\Desktop\Crown2026\.venv\Scripts\python.exe" manage.py shell -c @"
from django.urls import get_resolver
def walk(patterns, prefix=''):
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            walk(p.url_patterns, prefix + str(p.pattern))
        else:
            lookup = getattr(p, 'lookup_str', '')
            name = p.name or ''
            print((prefix + str(p.pattern)) + '\t' + name + '\t' + lookup)
walk(get_resolver().url_patterns)
"@ | Select-String -Pattern "billing|invoice|invoices|payment|payments|tuition|ledger|balance|statement|charge|charges|cash|deposit" -CaseSensitive:$false

Write-Host "`n== LANE 2 MAP: BACKEND FILE HITS ==" -ForegroundColor Cyan

$root = "$env:USERPROFILE\OneDrive\Desktop\Crown2026"
$keywords = @("billing","invoice","payment","tuition","ledger","balance","charge")

foreach ($k in $keywords) {
    Write-Host "`n--- KEYWORD: $k ---" -ForegroundColor Yellow
    Get-ChildItem -Path "$root\backend" -Recurse -Include "*.py" |
        Select-String -Pattern $k -CaseSensitive:$false |
        Where-Object { $_.Filename -notmatch "migrations|__pycache__|test_" } |
        Select-Object @{n='File';e={$_.Path.Replace("$root\",'')}}, LineNumber, Line |
        Select-Object -First 30 |
        Format-Table -AutoSize |
        Out-String -Width 200
}

Write-Host "`nLANE2_MAP=DONE" -ForegroundColor Green
