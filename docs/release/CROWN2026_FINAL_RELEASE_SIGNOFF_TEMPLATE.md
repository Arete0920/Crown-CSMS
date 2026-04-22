# Crown2026 Final Release Signoff Template

## Release rule
Release is forbidden unless every blocking lane is GREEN.

## Blocking lanes
- Security / repo controls
- Backend / runtime / OpenAPI / health / integrity
- Tenant isolation / RBAC
- Admissions -> enrollment -> billing -> attendance
- Sandbox admin redesigned dashboard proof
- Reporting / export / transcript
- Load / resilience
- Governance / evidence freshness

## Artifact checklist
- [ ] 00_release_certification_summary.json
- [ ] 00_release_gate_results.csv
- [ ] 02_backend_runtime_summary.json
- [ ] 03_playwright_summary.json
- [ ] 04_load_summary.json
- [ ] 06_phase2_summary.json
- [ ] 01_branch_protection.json
- [ ] 01_branch_protection_screenshot.png
- [ ] codeql-blocking-evidence.png
- [ ] dep-audit-blocking-evidence.png
- [ ] FINAL_RELEASE_SIGNOFF_PACKET.md

## Final disposition
- [ ] PASS
- [ ] FAIL

## Approval signatures
- Product Owner
- Core Platform Lead
- SIS Lead
- Modules Lead
- Frontend Lead
- Integration / Release Lead
