# Dev-Ready Punch List — Crown 2026

**Generated:** 2026-04-30
**Branch:** `readiness/sandbox-operator-freeze-20260427_222113`
**Source data:** `audit-artifacts/priority-07-hygiene-closure/20260430_182607/13_dashboard_metric_review.csv`
**Status:** 21 PASS / 48 REVIEW — this list covers the top-10 highest-impact REVIEW items

---

## How to Use This List

1. Pick a ticket by **Priority** order.
2. Check **Gap** — the specific signal(s) the automated review flagged.
3. Implement the fix per **Acceptance Criteria**.
4. Re-run the dashboard metric scan to confirm the row flips from `REVIEW` → `PASS`:

```powershell
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" `
     -File "scripts\execution\148_priority07_hygiene_closure.ps1"
```

<!-- markdownlint-disable-next-line MD029 -->
5. Close the ticket when CI artifact shows `PASS` for the file.

---

## Priority Ranking

| Priority | Area | Impact Rationale |
| --- | --- | --- |
| P0 | Shared template | Defect multiplies across every dashboard |
| P1 | Admin / Board dashboards | Highest operator + executive visibility |
| P2 | Admission / Attendance | Core daily operational traffic |
| P3 | Advancement | Fundraising reporting surface |
| P4 | Navigation config | Broken nav entry blocks all modules |
| P5 | Wizard route registry | Dead route = user-facing 404 |
| P6 | Wizard manifest | Manifest/route mismatch = silent breakage |
| P7 | FinanceSetupWizard | Highest page density, most cross-cutting |

---

## Item 1 — CrownDashboardTemplate (P0)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 4 |
| **Priority** | P0 — shared by all dashboards; fix once, benefits all |

**What "done" looks like:**

- `<KpiStrip … />` imported and rendered in the template layout
- A `dataSource` prop (or equivalent metadata comment block) added so the metric scanner can detect it
- `UsesKpiStrip=True` and `HasDataSourceMetadata=True` in next scan run
- No new console errors in browser dev-tools when any dashboard loads

**Acceptance check (automated):**

```powershell
$row = Import-Csv 'audit-artifacts\priority-07-hygiene-closure\<latest-run>\13_dashboard_metric_review.csv' |
       Where-Object { $_.File -like '*CrownDashboardTemplate*' }
$row.UsesKpiStrip    # must be True
$row.HasDataSourceMetadata  # must be True
$row.Status          # must be PASS
```

---

## Item 2 — AdminDashboard (P1)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/AdminDashboard.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 4 |
| **Priority** | P1 — highest admin operator visibility |

**What "done" looks like:**

- KpiStrip rendered with admin-relevant KPIs (active users, open incidents, system health)
- `dataSource` metadata annotation present
- Row status → `PASS` in scan

**Acceptance check (automated):** Same pattern as Item 1, filter on `*AdminDashboard*`.

---

## Item 3 — BoardDashboard (P1)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/BoardDashboard.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 4 |
| **Priority** | P1 — executive surface, board-level data |

**What "done" looks like:**

- KpiStrip rendered with board-relevant KPIs (enrollment totals, budget summary, advancement totals)
- `dataSource` metadata annotation present
- Row status → `PASS` in scan

**Acceptance check (automated):** Filter on `*BoardDashboard*`.

---

## Item 4 — AdmissionsDashboard (P2)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/AdmissionsDashboard.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 3 (domain), Dev 4 (KPI component wiring) |
| **Priority** | P2 — core daily operational traffic |

**What "done" looks like:**

- KpiStrip rendered with admissions KPIs (applications, enrollments, waitlist)
- `dataSource` metadata annotation present
- Row status → `PASS` in scan

**Acceptance check (automated):** Filter on `*AdmissionsDashboard*`.

---

## Item 5 — AttendanceDashboard (P2)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/AttendanceDashboard.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 2 (domain), Dev 4 (KPI component wiring) |
| **Priority** | P2 — core daily operational traffic |

**What "done" looks like:**

- KpiStrip rendered with attendance KPIs (daily rate, absentee count, tardy count)
- `dataSource` metadata annotation present
- Row status → `PASS` in scan

**Acceptance check (automated):** Filter on `*AttendanceDashboard*`.

---

## Item 6 — AdvancementDashboard (P3)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/AdvancementDashboard.jsx` |
| **Gap** | `UsesKpiStrip=False`, `HasDataSourceMetadata=False` |
| **Owner** | Dev 3 (domain), Dev 4 (KPI component wiring) |
| **Priority** | P3 — fundraising reporting surface |

**What "done" looks like:**

- KpiStrip rendered with advancement KPIs (campaign total, donor count, pledge outstanding)
- `dataSource` metadata annotation present
- Row status → `PASS` in scan

**Acceptance check (automated):** Filter on `*AdvancementDashboard*`.

---

## Item 7 — dashboardNavConfig (P4)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/components/navigation/dashboardNavConfig.js` |
| **Gap** | 31 cross-file references — needs completeness and consistency audit |
| **Owner** | Dev 4 |
| **Priority** | P4 — broken nav entry blocks user access to any module |

**What "done" looks like:**

- Every nav entry maps to a valid, existing route in the route registry
- No orphaned entries (route removed but nav entry left)
- No missing entries (dashboard added but not in nav)
- Manual smoke-test: click through all top-level nav items — each loads without 404

**Acceptance check (manual):**

```bash
# Verify all nav keys appear in route definitions
grep -oh "path: '[^']*'" src/components/navigation/dashboardNavConfig.js | \
  sort > nav_paths.txt
grep -oh "path: '[^']*'" src/routes/*.js | sort > route_paths.txt
diff nav_paths.txt route_paths.txt  # should be empty
```

---

## Item 8 — Wizard Route Registry (P5)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/routes/wizards.js` |
| **Gap** | 94 cross-file references — highest density; audit for dead routes and missing entries |
| **Owner** | Dev 4 (routes), Dev 5 (wizard page ownership) |
| **Priority** | P5 — dead route = user-facing 404 during wizard flow |

**What "done" looks like:**

- Every route entry in `wizards.js` has a corresponding `.jsx` page file
- Every wizard page file has a corresponding route in `wizards.js`
- No lazy-loaded component references to non-existent files
- E2E smoke: navigate to each wizard route, confirm it loads

**Acceptance check (automated):**

```powershell
# List route component paths vs actual files
$routes = Select-String -Path 'src\routes\wizards.js' -Pattern "component:.*import\('([^']+)'\)" |
          ForEach-Object { $_.Matches.Groups[1].Value }
$routes | ForEach-Object {
    $file = "src\$_.jsx"
    if (-not (Test-Path $file)) { Write-Warning "MISSING: $file" }
}
# Should produce zero warnings
```

---

## Item 9 — Wizard Manifest (P6)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/routes/wizard-manifest.js` |
| **Gap** | 35 cross-file references — manifest must match route registry 1-for-1 |
| **Owner** | Dev 4 (routes), Dev 5 (manifest ownership) |
| **Priority** | P6 — manifest/route mismatch causes silent wizard failure |

**What "done" looks like:**

- Every entry in `wizard-manifest.js` has a matching route key in `wizards.js`
- Every route key in `wizards.js` has a matching manifest entry
- Stale manifest entries (wizard removed) are deleted

**Acceptance check (manual):**

```bash
# Keys in manifest vs keys in route registry — diff should be empty
node -e "
  const m = require('./src/routes/wizard-manifest.js');
  const r = require('./src/routes/wizards.js');
  const mKeys = Object.keys(m).sort();
  const rKeys = r.map(w => w.key).sort();
  const missing = mKeys.filter(k => !rKeys.includes(k));
  const extra = rKeys.filter(k => !mKeys.includes(k));
  if (missing.length || extra.length) { console.error({missing, extra}); process.exit(1); }
  console.log('MANIFEST_MATCH_PASS');
"
```

---

## Item 10 — FinanceSetupWizard (P7)

| Field | Value |
| --- | --- |
| **File** | `frontend/dashboards/src/pages/wizards/FinanceSetupWizard.jsx` |
| **Gap** | 21 cross-file references — highest page density; hotspot for regressions |
| **Owner** | Dev 3 (finance domain), Dev 4 (wizard framework) |
| **Priority** | P7 — highest wizard page density means any change here ripples widely |

**What "done" looks like:**

- Full wizard flow completes without error in sandbox: steps 1→N → Submit
- No `console.error` or `console.warn` output during normal flow
- No static placeholder values (e.g., `TODO`, `PLACEHOLDER`, `0.00` as sentinel) visible to user
- If `HasStaticPlaceholderValue` scan flag exists for this file → must be `False`

**Acceptance check (manual + automated):**

1. Run hygiene scan; confirm `HasStaticPlaceholderValue=False` for this file.
2. Playwright smoke (or manual): complete wizard flow in sandbox; confirm no errors.
3. Check for placeholder text: `grep -n "TODO\|PLACEHOLDER\|TBD" src/pages/wizards/FinanceSetupWizard.jsx` — must be empty.

---

## Remaining 38 REVIEW Dashboards

The 38 remaining REVIEW dashboards (not in this top-10) share the same two gaps:
`UsesKpiStrip=False` and `HasDataSourceMetadata=False`.

Once **Item 1 (CrownDashboardTemplate)** is fixed, many of these will auto-resolve if
the template propagates KpiStrip to children. Re-run the hygiene scan after Item 1 is
merged to get a revised REVIEW count before triaging the remainder.

---

## Re-scan Command (run after each fix)

```powershell
pwsh -NonInteractive -WorkingDirectory "C:\w\crown_main_postmerge_verify" `
     -File "scripts\execution\148_priority07_hygiene_closure.ps1"
```

Artifact lands in:
`audit-artifacts/priority-07-hygiene-closure/<timestamp>/13_dashboard_metric_review.csv`

Target state: **69 PASS / 0 REVIEW**

---

## Azure-Gated Items (blocked — not in this punch list)

These cannot be closed until Azure secrets are provisioned:

| Item | Blocker |
| --- | --- |
| Azure SWA deploy | `AZURE_SWA_TOKEN` secret missing from repo |
| Azure backend deploy | `AZURE_CREDENTIALS` secret missing from repo |
| GitHub workflow green | Depends on both above |
| Runtime persona proof (TI-001..TI-010) | Needs live Azure environment |
| RBAC live role-matrix checks | Needs live Azure environment |

Notify Dev team: once `AZURE_SWA_TOKEN` and `AZURE_CREDENTIALS` are added to repo secrets,
run `scripts/execution/149_priority10_release_packet.ps1` to close the 3 Azure-pending
checklist items.
