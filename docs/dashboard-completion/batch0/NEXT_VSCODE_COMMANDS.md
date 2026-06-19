# Next VS Code Commands for Batch 0

Run from the PR #1121 worktree.

## 1. Confirm current state

```powershell
$WT='C:\Users\JMega\OneDrive\Desktop\Crown2026_worktrees\pr1121_dashboard_batch0_evidence_prep_20260619'
Set-Location $WT
git status --short
git rev-parse HEAD
```

## 2. Apply the known false-ready alignment fix

```powershell
$path='frontend\dashboards\src\config\dashboardRegistry.js'
$text=Get-Content $path -Raw
$text=$text.Replace("    releaseState: 'ready',", "    releaseState: 'draft',")
Set-Content $path $text -Encoding UTF8
git diff -- $path
```

Review the diff before committing. It should only change Dashboard Certification Center from ready to draft.

## 3. Re-run frontend checks

```powershell
Set-Location "$WT\frontend\dashboards"
npm run test:unit -- src/tests/releaseReadinessEvidenceContracts.test.js
npm run test:unit -- src/config/dashboardTemplateContract.test.js
npm run test:unit -- src/config/dashboardTemplateLiveMetadata.test.js
npm run build
```

## 4. Re-run browser proof with backend running

Start backend in a separate terminal first, then rerun the browser capture for dashboard-certification-center.

Expected improvement:

- no API 502s during browser capture
- screenshot/trace artifact refreshed
- browser-proof.json updated

## 5. Commit only if checks pass

```powershell
Set-Location $WT
git status --short
git add frontend/dashboards/src/config/dashboardRegistry.js
git add docs/dashboard-completion/batch0
git add audit-artifacts/dashboard-completion/browser-proof
git commit -m "docs(batch0): refresh dashboard certification center proof after stack alignment"
git push origin HEAD:feat/dashboard-batch0-evidence-prep-20260619
```

Do not mark any dashboard complete until independent review and matrix promotion exist.
