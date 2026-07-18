#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ["GITHUB_TOKEN"]
run_id = os.environ["GITHUB_RUN_ID"]
sha = os.environ.get("CERTIFIED_SOURCE_SHA", os.environ.get("GITHUB_SHA", "unknown"))
status = os.environ.get("JOB_STATUS", "unknown")
run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
summary_file = Path("audit-artifacts/live-runtime-certification/current/certification-summary.md")
tenant_file = Path("audit-artifacts/tenant-context/current/tenant-context-runtime-proof.json")
summary = summary_file.read_text(encoding="utf-8")[:6000] if summary_file.exists() else "Certification summary was not produced."
tenant = tenant_file.read_text(encoding="utf-8")[:3000] if tenant_file.exists() else "Tenant-context evidence was not produced."
body = f"""## Automated live-runtime evidence result

- Workflow status: **{status.upper()}**
- Certified source SHA: `{sha}`
- Run: {run_url}
- Expected artifacts: `live-runtime-certification-evidence-*`, `tenant-context-runtime-evidence-*`, and Playwright report

### Certification summary

{summary}

### Tenant-context excerpt

```json
{tenant}
```

A successful workflow is evidence for review, not automatic production authorization. A failed workflow must be repaired from its exact run evidence.
"""
for issue in (1274, 1276, 1287, 1351, 1275, 1374):
    url = f"https://api.github.com/repos/{repo}/issues/{issue}/comments"
    req = Request(url, data=json.dumps({"body": body}).encode(), method="POST", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "crown-live-evidence-publisher"})
    with urlopen(req, timeout=30) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"issue {issue} comment failed: {response.status}")
