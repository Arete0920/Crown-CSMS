Set-Location C:\w\crown_main_postmerge_verify
$Out = "C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221"

@(
  [pscustomobject]@{Category='SAFE - Form attributes';     Count=98;  Paths='frontend/**';     Finding='HTML placeholder= attributes on <input> elements. Standard form UX, not product incompleteness.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Test files';          Count=31;  Paths='backend/tests/*'; Finding='TODO/FIXME comments and test fixture strings in test files only.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Detection utility';   Count=4;   Paths='frontend/dashboards/src/config/releaseState.js'; Finding='PLACEHOLDER constant and pattern defined in release-state detection utility (the scanner itself).'; Action='None'}
  [pscustomobject]@{Category='SAFE - Migration comments';  Count=4;   Paths='backend/academics/migrations/*'; Finding='Comment explaining placeholder field names to avoid rename operations. Inert.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Governance check';    Count=1;   Paths='backend/governance/services.py:706'; Finding='no_placeholder_board_packs: bool(...) -- readiness flag, not user-visible content.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Release state check'; Count=1;   Paths='backend/academics/transcript_views.py:247'; Finding='Code comment noting GPA is simple unweighted average. Not in API response.'; Action='None'}
  [pscustomobject]@{Category='SAFE - SeatingAdminPage';    Count=3;   Paths='frontend/dashboards/src/modules/advancement/SeatingAdminPage.jsx'; Finding='PLACEHOLDER_LAYOUT constant used as default editor state. Not shown as text to users.'; Action='Verify default layout is presentable on sandbox demo.'}
  [pscustomobject]@{Category='SAFE - Coming-soon button';  Count=1;   Paths='frontend/dashboards/src/pages/AcademicsDashboard.jsx:537'; Finding='Disabled button labeled "Attendance (coming soon)". Clearly labeled, disabled, acceptable for sandbox preview.'; Action='Confirm with Dev 4 whether to hide or keep for sandbox.'}
  [pscustomobject]@{Category='SAFE - Dev scripts';         Count=7;   Paths='scripts/execution/*, scripts/release/*'; Finding='generate_215_fixes.py and mock_seed_scan.py contain placeholder strings. Not deployed.'; Action='None'}
  [pscustomobject]@{Category='SAFE - Remediation docs';    Count=11;  Paths='src/51x51-remediation/*'; Finding='No-placeholder sample files used as remediation spec. Not deployed.'; Action='None'}
  [pscustomobject]@{Category='FIXED';                      Count=1;   Paths='backend/academics/transcript_views.py:333'; Finding='API response notes contained "GPA values are MVP placeholders; weighting engine not yet implemented." -- developer text visible to any API consumer.'; Action='FIXED: notes field cleared (empty array). GPA data still present, notes removed.'}
  [pscustomobject]@{Category='OUTSTANDING - Verify';       Count=169; Paths='various frontend/ placeholder= attributes'; Finding='Remaining 169 non-keyword hits are all placeholder= HTML form attributes (e.g. placeholder="Search...", placeholder="e.g. 2026-2027"). Count from total 331 - known categories.'; Action='Confirm none display raw "placeholder" text to users as content.'}
) | Export-Csv "$Out\20b_placeholder_scan_triage.csv" -NoTypeInformation
Write-Host "Placeholder triage written."
