# 901 dashboard pytest observability note

Current operational blocker: `901_executive_sandbox_gate.ps1` reaches `backend-check-complete` and then stalls during `python -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py -q` with an empty dashboard sample gate log.

Next local diagnostic command:

```powershell
Set-Location 'C:\Users\JMega\OneDrive\Desktop\Crown2026_main_901'
$env:PYTHONFAULTHANDLER='1'
$env:PYTHONUNBUFFERED='1'
python -X faulthandler -m pytest backend\crown_api\tests\test_dashboard_snapshot_summary_api.py -vv -s --tb=long --setup-show --durations=20
```

If it hangs, install/use pytest-timeout:

```powershell
python -m pip install pytest-timeout
python -X faulthandler -m pytest backend\crown_api\tests\test_dashboard_snapshot_summary_api.py -vv -s --tb=long --setup-show --durations=20 --timeout=90 --timeout-method=thread
```
