Set-Location C:\w\crown_main_postmerge_verify
$Out = "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221"

@(
  [pscustomobject]@{Category='SAFE - Test files';             Count=25; Paths='frontend/dashboards/tests/*'; Finding='Anti-pattern strings in test fixture assertions. Not visible to users.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Dev-gated console.logs'; Count=8;  Paths='frontend/dashboards/src/utils/requestTracing.js'; Finding='All console.log calls are inside if (!import.meta.env.DEV) return; guard. Will not emit in production builds.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Playwright report';      Count=3;  Paths='frontend/dashboards/playwright-report/*'; Finding='Generated test report HTML. Not part of deployed app.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Apple Pass service';     Count=1;  Paths='services/wallet/apple-pass-service/*'; Finding='Wallet service not deployed in Phase 2 scope.'; Action='None'}
  [pscustomobject]@{Category='FIXED - Dashboard accent tokens'; Count=9; Paths='frontend/dashboards/src/config/dashboardTemplates/*.js'; Finding='9 dashboard templates used accent:navy (dark) color token instead of CROWN royal token.'; Action="FIXED: replaced accent:'navy' with accent:'royal' in all 9 template files."}
  [pscustomobject]@{Category='NEEDS DESIGN REVIEW - Login page dark theme'; Count=4; Paths='frontend/dashboards/src/pages/LoginPage.jsx (lines 208-433)'; Finding='Login page uses dark navy gradient backgrounds (--lp-navy-900, --lp-navy-700, radial-gradient #1E4A7A). Intentional brand design (dark-on-navy login) vs CROWN light royal standard.'; Action='Dev 4 to confirm: intentional dark login branding or convert to light royal?'}
  [pscustomobject]@{Category='NEEDS REVIEW - BillingDashboard'; Count=1; Paths='frontend/dashboards/src/pages/BillingDashboard.jsx'; Finding='1 anti-pattern hit -- verify it is not a user-visible dark treatment.'; Action='Dev 4 to review BillingDashboard.jsx for any dark/navy hardcoded colors.'}
  [pscustomobject]@{Category='SAFE - Login template backend'; Count=1;  Paths='backend/crown_api/templates/registration/login.html:24'; Finding='color: #333 in Django login template (used for superuser admin login, not student-facing). Acceptable.'; Action='None'}
) | Export-Csv "$Out\21b_ui_antipattern_triage.csv" -NoTypeInformation
Write-Host "UI anti-pattern triage written."
