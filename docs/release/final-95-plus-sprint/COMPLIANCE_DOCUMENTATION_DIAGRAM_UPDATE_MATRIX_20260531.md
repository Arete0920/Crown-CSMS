# CROWN Compliance Documentation and Diagram Update Matrix - 2026-05-31

Status: ACTIVE COMPLIANCE-READINESS CONTROL ARTIFACT
Authority: Non-shipping control artifact until completed, reviewed, and promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This matrix identifies the Mermaid diagrams, reports, compliance files, trust packets, and release artifacts that must be updated before CROWN can be treated as compliance-ready.

Compliance readiness is not achieved by policy text alone. It requires diagrams, data-flow maps, role/permission matrices, subprocessors, retention maps, support access controls, incident response, backup/restore proof, runtime enforcement evidence, and legal/product-owner acceptance.

## Current decision

Compliance readiness: NOT READY.

Reason: Existing compliance packet is documented but not legal-signed, and proof items remain open. Diagrams are useful but describe governed/intended architecture and must be refreshed to match current release gates, open PRs, open issues, residual risks, and compliance evidence.

## Files requiring review or update

| File / Artifact | Current role | Required update | Status |
|---|---|---|---|
| `docs/compliance/CROWN_COMPLIANCE_CUSTOMER_READINESS_PACKET_20260529.md` | Existing compliance/customer-readiness policy packet | Convert from documented policy packet into evidence-backed compliance packet with legal/product-owner signoff references | NOT DONE |
| `docs/architecture/CROWN_PRINTED_BINDER_MERMAID_VISUALS_20260529.md` | Binder-ready Mermaid architecture visuals | Add compliance-specific diagrams for FERPA/COPPA/CIPA/data-retention/subprocessor/support-access/incident/backup flows; update release artifact references to final sprint controls | NOT DONE |
| `docs/release/final-95-plus-sprint/COMPLIANCE_CUSTOMER_READINESS_AUDIT_20260530.md` | Final sprint compliance audit | Update after evidence exists; add links to completed compliance packets and diagrams | NOT DONE |
| `docs/release/final-95-plus-sprint/RESIDUAL_RISK_REGISTER_20260530.md` | Residual risk register | Map compliance residual risks to final artifacts and owners after execution | NOT DONE |
| `docs/release/final-95-plus-sprint/FINAL_IP_CLEAN_ROOM_ORIGINALITY_PACKET.md` | IP/originality release gate | Attach scan evidence, module originality review, asset review, dependency/license packet, legal review status | NOT DONE |
| `docs/release/final-95-plus-sprint/FINAL_SIGNOFF_TEMPLATE_20260530.md` | Final signoff template | Require compliance/legal/customer-trust approvals before GO | NOT DONE |
| `docs/release/final-95-plus-sprint/SANDBOX_READY_GATE_20260601.md` | Sandbox readiness gate | Add compliance-safe sandbox evidence links: synthetic data, no real student data, sandbox limitation statement | NOT DONE |
| `docs/release/final-95-plus-sprint/PRODUCTION_RELEASE_ROADMAP_20260701.md` | Production roadmap | Add compliance diagram/documentation completion as explicit GO prerequisite | NOT DONE |

## Required Mermaid diagram additions

The existing Mermaid binder should be expanded or accompanied by a new compliance Mermaid file with these diagrams:

| Diagram | Purpose | Required status |
|---|---|---|
| Student data lifecycle flow | Capture collection, access, processing, export, retention, deletion/anonymization, and audit | NOT DONE |
| FERPA access/disclosure flow | Show parent/student/school official/support/vendor access paths and disclosure logging | NOT DONE |
| COPPA school/parent consent posture flow | Show under-13 student access, school-directed use, parent notice, collection limits, deletion/export routing | NOT DONE |
| CIPA / online safety boundary flow | Show online classroom/Teams/MS365 learning-continuity safety boundaries and school-admin responsibilities | NOT DONE |
| Tenant/RBAC/object-permission compliance flow | Show tenant, role, object, and field sensitivity controls for every sensitive domain | NOT DONE |
| Support access / break-glass flow | Show approval, time-bound access, audit, incident review, and export restrictions | NOT DONE |
| Incident response flow | Show detection, triage, containment, affected-tenant analysis, customer notice, remediation, closure report | NOT DONE |
| Backup/restore and retention flow | Show backup creation, encryption, access control, restore test, retention/expiration, deletion alignment | NOT DONE |
| Subprocessor/data-transfer flow | Show vendors, purposes, data categories, contract/DPA status, customer notice/change control | NOT DONE |
| Sandbox-production separation flow | Show synthetic data, demo credentials, reset, no production dumps, and limitation labeling | NOT DONE |
| IP clean-room/originality flow | Show competitor research quarantine, abstraction, original design, scan evidence, legal review | NOT DONE |

## Required reports and evidence files

| Report / Evidence Packet | Purpose | Status |
|---|---|---|
| `FINAL_CUSTOMER_TRUST_PACKET.md` | Customer-facing compliance/privacy/security summary | NOT DONE |
| `FINAL_PRIVACY_SECURITY_COMPLIANCE_SUMMARY.md` | Internal/external compliance position summary | NOT DONE |
| `FINAL_DATA_INVENTORY_AND_CLASSIFICATION.md` | Data categories by model/domain and sensitivity | NOT DONE |
| `FINAL_RETENTION_PURGE_PACKET.md` | Retention classes, deletion/anonymization procedure, legal hold/purge controls | NOT DONE |
| `FINAL_SUBPROCESSOR_REGISTER.md` | Vendor/service/data category/region/contract status/change notice | NOT DONE |
| `FINAL_DPA_TEMPLATE_REVIEW.md` | DPA/customer contract checklist and legal review status | NOT DONE |
| `FINAL_SUPPORT_ACCESS_PACKET.md` | Support approval, access logs, impersonation/break-glass rules | NOT DONE |
| `FINAL_INCIDENT_RESPONSE_TABLETOP.md` | Incident response scenario/test evidence | NOT DONE |
| `FINAL_BACKUP_RESTORE_PROOF.md` | Restore test and RPO/RTO proof | NOT DONE |
| `FINAL_SANDBOX_DATA_POLICY.md` | Synthetic/demo/no-real-data enforcement and limitations | NOT DONE |
| `FINAL_ACCESSIBILITY_PACKET.md` | Accessibility proof and exceptions | NOT DONE |
| `FINAL_M365_TEAMS_READINESS_PACKET.md` | Entra/Graph/Teams/MS365 readiness and failure handling | NOT DONE |
| `FINAL_PAYMENT_SECURITY_SCOPE_PACKET.md` | PCI/payment provider boundary and no-card-data posture | NOT DONE |
| `FINAL_REPORTING_EXPORT_PRIVACY_PACKET.md` | Export/report role/tenant/field-level privacy controls | NOT DONE |
| `FINAL_IP_CLEAN_ROOM_ORIGINALITY_REVIEW.md` | Originality scan/review/legal status | NOT DONE |

## Compliance control checklist

| Control | Required proof | Status |
|---|---|---|
| FERPA education-record access | Parent/student/school official rights and access rules mapped to CROWN roles | NOT DONE |
| FERPA disclosure logging | Access/disclosure audit trail and export logging proof | NOT DONE |
| FERPA school official/vendor posture | Direct control, legitimate educational interest, redisclosure limits, contract/DPA proof | NOT DONE |
| COPPA under-13 posture | School-directed use, parent notice/consent model, no behavioral ads, minimal collection | NOT DONE |
| CIPA boundary | Internet safety/online behavior boundaries for online classroom or school-managed device contexts | NOT DONE |
| Data minimization | Collection limited to school-operational purpose | NOT DONE |
| Retention/deletion | Retention class and deletion/anonymization path per domain | NOT DONE |
| Subprocessors | Current vendor register and DPA/subprocessor notices | NOT DONE |
| Support access | Least-privilege/time-bound/audited support access | NOT DONE |
| Incident response | Tabletop/test and customer notification workflow | NOT DONE |
| Backup/restore | Actual restore proof, not only policy | NOT DONE |
| Sandbox separation | Synthetic data only and no production secrets/dumps | NOT DONE |
| Accessibility | Core role journey accessibility proof | NOT DONE |
| IP originality | Clean-room scans, asset/copy review, dependency/license review | NOT DONE |

## Required VS Code scan/evidence commands

Run the general final sprint evidence pack first:

```powershell
git checkout main
git pull
git status --short --branch
```

Then run:

```text
docs/release/final-95-plus-sprint/VSCODE_SINGLE_BLOCK_EVIDENCE_RUN_20260530.md
```

Then run IP clean-room scans from:

```text
docs/release/final-95-plus-sprint/FINAL_IP_CLEAN_ROOM_ORIGINALITY_PACKET.md
```

Then create compliance evidence root:

```powershell
$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = "audit-artifacts\final-95-plus-sprint\compliance-docs-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== COMPLIANCE DOC INVENTORY ===" | Tee-Object "$base\01_compliance_doc_inventory.txt"
Get-ChildItem docs -Recurse -File | Where-Object {
  $_.FullName -match 'compliance|privacy|security|retention|incident|backup|restore|subprocessor|DPA|FERPA|COPPA|CIPA|Mermaid|diagram|binder|trust|sandbox'
} | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\01_compliance_doc_inventory.txt"

"=== MERMAID INVENTORY ===" | Tee-Object "$base\02_mermaid_inventory.txt"
git grep -n -i -- '```mermaid' -- docs 2>&1 | Tee-Object -Append "$base\02_mermaid_inventory.txt"

"=== COMPLIANCE KEYWORD SCAN ===" | Tee-Object "$base\03_compliance_keyword_scan.txt"
$terms = @('FERPA','COPPA','CIPA','DPA','subprocessor','retention','purge','incident response','support access','backup','restore','sandbox data','student privacy','education records','directory information','school official')
foreach ($term in $terms) {
  "=== $term ===" | Tee-Object -Append "$base\03_compliance_keyword_scan.txt"
  git grep -n -i -- "$term" -- docs backend frontend ':!node_modules' ':!.venv' ':!dist' ':!build' 2>&1 | Tee-Object -Append "$base\03_compliance_keyword_scan.txt"
}

"=== COMPLIANCE DOC MANIFEST ===" | Tee-Object "$base\99_manifest.txt"
"timestamp=$stamp" | Tee-Object -Append "$base\99_manifest.txt"
"repo_head=$(git rev-parse HEAD)" | Tee-Object -Append "$base\99_manifest.txt"
"repo_branch=$(git branch --show-current)" | Tee-Object -Append "$base\99_manifest.txt"
Get-ChildItem $base | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\99_manifest.txt"

Write-Host "COMPLIANCE_DOC_EVIDENCE_ROOT=$base"
```

## Decision rule

CROWN is not compliance-ready until:

1. this matrix is closed;
2. the existing compliance packet is updated from documented-only to evidence-backed;
3. required Mermaid diagrams and reports are current;
4. runtime enforcement proof exists;
5. legal/product-owner review is attached;
6. sandbox and production release authorities reference the final compliance evidence.

## Current status

Compliance documentation and diagram readiness: NOT DONE.

Release impact: NO-GO for unrestricted production and NO-GO for compliance-ready claims until evidence is attached and reviewed.
