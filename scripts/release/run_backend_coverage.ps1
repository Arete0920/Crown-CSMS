#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python -m pip install coverage
coverage run backend/manage.py test
coverage report
coverage html -d audit-artifacts/coverage-html
