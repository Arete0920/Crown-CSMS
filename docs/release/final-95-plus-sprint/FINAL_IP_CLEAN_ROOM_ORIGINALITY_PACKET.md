# CROWN Final IP Clean-Room and Originality Packet

Status: ACTIVE RELEASE BLOCKER PACKET
Authority: Non-shipping control artifact until completed, reviewed, and promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This packet exists to reduce IP, copyright, trade-secret, competitor-copy, and market-research contamination risk before sandbox, buyer-facing, or production release.

CROWN may learn from lawful market research and public industry patterns. CROWN must not copy competitor protected expression, source code, private documentation, screenshots, brand identity, confidential workflows, or trade secrets.

## Release decision

Current status: NOT DONE

Production release remains NO-GO until this packet is completed or formally accepted by counsel with documented rationale.

Sandbox release remains NO-GO for any customer/buyer-facing demo that contains unreviewed competitor-derived text, layouts, assets, screenshots, workflows, or artifacts.

## Legal-reference basis

This packet is built around these control principles:

1. Copyright may protect original works of authorship fixed in a tangible medium, but does not extend to ideas, procedures, processes, systems, methods of operation, concepts, principles, or discoveries.
2. Competitor research may inform generalized market needs and industry expectations.
3. Competitor expression, code, copy, screenshots, assets, and confidential/private materials must not be copied.
4. Trade-secret risk must be avoided by excluding confidential, non-public, improperly obtained, NDA-covered, or otherwise restricted information.
5. Final legal clearance should be performed by qualified counsel before marketplace release.

## Clean-room rule

Every competitor-derived observation must pass through this abstraction chain before implementation:

```text
raw observation
-> generalized market need
-> CROWN-specific product requirement
-> original CROWN workflow design
-> original CROWN UI/copy/code
-> evidence of independent implementation
```

No implementation work should be driven directly by a competitor screenshot, copied wording, private demo recording, internal manual, database schema, CSS, source code, report design, or proprietary artifact.

## Prohibited source material

Do not use any of the following in CROWN implementation unless a written license/permission review exists:

- competitor source code;
- copied HTML/CSS/JavaScript;
- copied dashboard layouts or screens;
- copied icons, images, screenshots, videos, logos, graphics, or brand assets;
- copied marketing copy, onboarding copy, help text, error messages, labels, or report language;
- competitor private documentation;
- NDA-protected demo material;
- proprietary customer lists, pricing sheets, implementation guides, reports, or schemas;
- private process documentation;
- trade-secret or confidential information from any source.

## Permitted research use

The following are acceptable if converted into original CROWN-specific design:

- common industry workflow expectations;
- public feature-category observations;
- generalized role needs;
- public operational pain points;
- common KPI categories;
- broadly known school-management processes;
- public pricing/category awareness without copying copy or structure;
- comparison insights summarized in neutral, original language.

## Competitor research quarantine

Raw competitor research must be kept out of implementation paths.

Quarantine requirements:

| Material type | Rule |
|---|---|
| Screenshots | Research-only; not copied into product/docs/marketing |
| Competitor text | Research-only; not reused as UI/copy/help/marketing content |
| Videos/demos | Summarize into neutral requirements only |
| PDFs/manuals | Do not paste into implementation docs; abstract into requirements |
| Private/NDA material | Do not use unless legal review explicitly permits |
| Pricing/packaging | Use only for strategic awareness, not copied packaging/copy |

## Originality certification by module

Every production-visible module must receive an originality row before release.

| Module | Original workflow? | Original UI/copy? | No competitor assets? | No competitor code? | No private/trade-secret material? | Evidence | Status |
|---|---|---|---|---|---|---|---|
| Identity / RBAC / Tenant | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Core SIS Student Records | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Admissions | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Enrollment / Re-enrollment | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Billing / Tuition | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Payments / Ledger | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Financial Aid | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Attendance | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Gradebook | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Scheduling | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Communications / CRM | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| LMS / Online Classroom | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Curriculum / Lesson Plans | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Student Care / Discipline / Counseling | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Health Office | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Transportation | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Food Service | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| HR | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Facilities | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Safety / Security | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Fine Arts | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Library / Media | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Extended Care / Aftercare | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Summer Camp | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Little Lambs | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Spiritual Life / Service Hours | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Advancement / Alumni | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Board / Governance | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |
| Platform Operations | TBD | TBD | TBD | TBD | TBD | TBD | NOT DONE |

## Repo scan requirements

Run from repo root and capture outputs into the final evidence root.

### Competitor-name scan

```powershell
$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = "audit-artifacts\final-95-plus-sprint\ip-clean-room-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$competitors = @(
  "Blackbaud",
  "FACTS",
  "RenWeb",
  "PowerSchool",
  "Veracross",
  "Finalsite",
  "TADS",
  "SchoolAdmin",
  "Ravenna",
  "Alma",
  "Gradelink",
  "FACTS SIS",
  "Blackbaud Education"
)

foreach ($term in $competitors) {
  "=== Searching for $term ===" | Tee-Object -Append "$base\01_competitor_name_scan.txt"
  git grep -n -i -- "$term" -- . ':!node_modules' ':!.venv' ':!dist' ':!build' ':!.git' 2>&1 | Tee-Object -Append "$base\01_competitor_name_scan.txt"
}
```

### Copyright/source contamination scan

```powershell
$patterns = @(
  "all rights reserved",
  "copyright",
  "copied from",
  "borrowed from",
  "template from",
  "screenshot from",
  "powered by",
  "competitor",
  "blackbaud",
  "renweb",
  "facts sis",
  "powerschool",
  "veracross"
)

foreach ($pattern in $patterns) {
  "=== Searching for $pattern ===" | Tee-Object -Append "$base\02_source_contamination_scan.txt"
  git grep -n -i -- "$pattern" -- . ':!node_modules' ':!.venv' ':!dist' ':!build' ':!.git' 2>&1 | Tee-Object -Append "$base\02_source_contamination_scan.txt"
}
```

### Asset scan

```powershell
"=== IMAGE/ASSET INVENTORY ===" | Tee-Object "$base\03_asset_inventory.txt"
Get-ChildItem -Recurse -File | Where-Object {
  $_.FullName -notmatch '\\node_modules\\|\\.venv\\|\\dist\\|\\build\\|\\.git\\' -and
  $_.Extension -match '\.(png|jpg|jpeg|gif|svg|webp|ico|pdf|mp4|mov)$'
} | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\03_asset_inventory.txt"
```

### Dependency license baseline

```powershell
"=== PYTHON DEPENDENCIES ===" | Tee-Object "$base\04_dependency_license_baseline.txt"
if (Test-Path "backend\requirements.txt") { Get-Content "backend\requirements.txt" | Tee-Object -Append "$base\04_dependency_license_baseline.txt" }

"=== FRONTEND PACKAGE ===" | Tee-Object -Append "$base\04_dependency_license_baseline.txt"
if (Test-Path "frontend\dashboards\package.json") { Get-Content "frontend\dashboards\package.json" | Tee-Object -Append "$base\04_dependency_license_baseline.txt" }
```

### IP evidence manifest

```powershell
"=== IP CLEAN ROOM MANIFEST ===" | Tee-Object "$base\99_manifest.txt"
"timestamp=$stamp" | Tee-Object -Append "$base\99_manifest.txt"
"repo_head=$(git rev-parse HEAD)" | Tee-Object -Append "$base\99_manifest.txt"
"repo_branch=$(git branch --show-current)" | Tee-Object -Append "$base\99_manifest.txt"
Get-ChildItem $base | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\99_manifest.txt"

Write-Host "IP_CLEAN_ROOM_EVIDENCE_ROOT=$base"
```

## Required review actions

1. Review every competitor-name hit.
2. Review every copyright/source contamination hit.
3. Confirm whether each hit is harmless, historical, research-only, dependency-related, or a remediation item.
4. Review asset inventory for any competitor screenshot, logo, icon, graphic, PDF, or video.
5. Review dependency licenses and produce an SBOM/license packet before production release.
6. Fill the module originality certification table.
7. Obtain legal review before marketplace release.

## Required closure artifacts

- `FINAL_IP_CLEAN_ROOM_ORIGINALITY_REVIEW.md`
- `FINAL_COMPETITOR_RESEARCH_QUARANTINE_STATEMENT.md`
- `FINAL_UI_COPY_ORIGINALITY_REVIEW.md`
- `FINAL_ASSET_ORIGINALITY_REVIEW.md`
- `FINAL_DEPENDENCY_LICENSE_SBOM_PACKET.md`
- `FINAL_TRADE_SECRET_NON_USE_CERTIFICATION.md`
- `FINAL_LEGAL_REVIEW_PLACEHOLDER.md`

## Closure standard

This packet can move from NOT DONE to PASS only when:

1. scans are run on the candidate SHA;
2. findings are reviewed;
3. risky content is removed or documented as permitted;
4. module originality rows are completed;
5. dependency/license packet is complete;
6. legal review is completed or explicitly marked pending with release blocked.

## Current decision

IP clean-room and originality readiness: NOT DONE.

Unrestricted production release remains NO-GO until this packet is closed or formally accepted by counsel.
