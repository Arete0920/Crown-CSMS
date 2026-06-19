# Browser Proof: compliance-audit

Dashboard key: compliance-audit  
Date: 2026-06-19  
Route: `/compliance-audit-dashboard`  
Screenshot: `docs/dashboard-completion/browser-proof/compliance-audit-20260619.png`

## Runtime setup

- Frontend server: `npm run dev -- --host 127.0.0.1 --port 3000`
- Browser runtime: Playwright Chromium
- Seeded role: `crown_compliance`
- Seeded school id: `19801b59-8c05-4c84-9312-5d792e4e839d`

## Observed result

- Browser title rendered: `Good morning, Compliance Team!`
- Browser metrics rendered:
  - `Active Audit Proof Streams` = `TBD`
  - `Controls Passing` = `TBD`
  - `Open Findings` = `TBD`
  - `Reviews Due (30d)` = `TBD`
- Browser disclosure rendered: `Fallback dashboard records are explicitly labeled. Frontend fallback dashboard data (/api/v1/dashboards/compliance-audit/summary).`

## Interpretation

This browser proof shows the route is renderable for the compliance role and that the current non-certified state is disclosed as fallback proof data when the summary API is unavailable in the local browser lane.

This is browser-rendered title/metrics proof only. It does **not** certify a live compliance truth source, independent review, or matrix promotion.

## Command output excerpt

```json
{
  "title": "Good morning, Compliance Team!",
  "metrics": [
    { "label": "Active Audit Proof Streams", "value": "TBD" },
    { "label": "Controls Passing", "value": "TBD" },
    { "label": "Open Findings", "value": "TBD" },
    { "label": "Reviews Due (30d)", "value": "TBD" }
  ],
  "fallbackText": [
    "Fallback dashboard records are explicitly labeled. Frontend fallback dashboard data (/api/v1/dashboards/compliance-audit/summary)."
  ]
}
```
