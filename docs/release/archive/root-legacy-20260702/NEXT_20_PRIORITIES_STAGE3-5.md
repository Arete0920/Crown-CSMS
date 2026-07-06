# NEXT 20 PRIORITIES: Stage 3-5 (Inventory Completion → Final Authority Signoff)

## OVERVIEW
These 20 priorities focus on completing Stage 3 (surface inventory classification), Stage 4 (production currentness proof), and Stage 5 (final authority signoff). All 20 will be executed in sequence with full evidence and commit trail.

---

## PHASE 1: Missing Surface Integration (1-5)

### Priority 1: Extract Missing Surfaces from Validator
**Objective:** Parse discovered-surface-coverage validator output and identify exactly which 160 surfaces are missing from inventory.  
**Method:** Run validator → extract missing surface list → parse into structured format  
**Success Criteria:** Complete list of 160 missing surfaces with path and category

### Priority 2: Classify Missing Surfaces (P0/P1/P2/P3)
**Objective:** Assign priority classification to each of 160 missing surfaces using same pattern rules.  
**Method:** Apply P0_AUTH/P1_CORE/P2_OPS/P3_ADMIN patterns to missing surfaces  
**Success Criteria:** 160 surfaces classified with release_blocking flag

### Priority 3: Add Missing Surfaces to Inventory
**Objective:** Merge 160 classified missing surfaces into crown-test-inventory.json.  
**Method:** Read current inventory → add missing surfaces → verify 990 total items → commit  
**Success Criteria:** Inventory JSON contains all 990 items (830 + 160)

### Priority 4: Validate P0/P1 Coverage Completeness
**Objective:** Verify all critical P0 (auth/RBAC/tenant) and P1 (academics/students) surfaces are covered.  
**Method:** Extract P0/P1 items → check against known critical components → identify gaps  
**Success Criteria:** P0 coverage 100%, P1 coverage 100%

### Priority 5: Document Surface Integration Decision
**Objective:** Create evidence document showing reclassification from 830-all-blocking to 59-release-blocking with 160 new surfaces.  
**Method:** Create SURFACE_CLASSIFICATION_AUDIT.md with rationale and audit trail  
**Success Criteria:** Document committed with classification methodology

---

## PHASE 2: Production Proof Implementation (6-10)

### Priority 6: Implement Production Health Endpoint Probe
**Objective:** Create/enable build_sha endpoint that production health probe can query.  
**Method:** Add endpoint to backend health check route returning build_sha  
**Success Criteria:** Endpoint returns valid build_sha matching current HEAD

### Priority 7: Create Production Baseline Snapshot
**Objective:** Document current production build_sha and capture baseline state.  
**Method:** Query production health endpoint → record build_sha → create PRODUCTION_BASELINE.md  
**Success Criteria:** Baseline snapshot created with timestamp and build_sha

### Priority 8: Validate Gate Production Probe Integration
**Objective:** Verify final release gate can query production probe and compare build_sha.  
**Method:** Test production probe flag in gate, verify it detects mismatches  
**Success Criteria:** Gate shows production currentness pass/fail based on build_sha match

### Priority 9: Document Production Currentness Proof
**Objective:** Create evidence showing production and staging are aligned or rationale for divergence.  
**Method:** Compare production build_sha with current HEAD → document findings  
**Success Criteria:** PRODUCTION_CURRENTNESS_PROOF.md created and committed

### Priority 10: Prepare Production Probe for Release
**Objective:** Enable production probe flag in final gate.  
**Method:** Update gate to run with full production probe (not skipped)  
**Success Criteria:** Gate runs with production check enabled, documenting current status

---

## PHASE 3: P0 Security & Isolation Verification (11-15)

### Priority 11: Audit RBAC Implementation Against Proof
**Objective:** Verify RBAC implementation matches release authority proof document requirements.  
**Method:** Extract RBAC proof from docs/release/ → compare with code implementation → create audit report  
**Success Criteria:** RBAC_AUDIT_REPORT.md created showing compliance

### Priority 12: Verify Tenant Isolation Implementation
**Objective:** Confirm tenant isolation layer is implemented and tested.  
**Method:** Extract tenant isolation proof → check code implementation → verify test coverage  
**Success Criteria:** TENANT_ISOLATION_PROOF.md created showing isolation validation

### Priority 13: Verify User Authentication Layer
**Objective:** Confirm Azure AD/identity provider integration is implemented and tested.  
**Method:** Check msauth implementation → verify token validation → check decorator coverage  
**Success Criteria:** AUTH_PROOF.md created with implementation validation

### Priority 14: Verify Route Guard Implementation
**Objective:** Confirm PermissionGate and RoleRouteGuard are protecting all protected routes.  
**Method:** Audit frontend routes → check guard decorators → verify permission checks  
**Success Criteria:** ROUTE_GUARD_AUDIT.md created showing protection coverage

### Priority 15: Create P0_SECURITY_PROOF Document
**Objective:** Create comprehensive security proof combining RBAC/Tenant/Auth/Routes.  
**Method:** Merge all P0 audit reports into single PROOF document  
**Success Criteria:** P0_SECURITY_PROOF.md created and committed

---

## PHASE 4: Final Release Control Documentation (16-20)

### Priority 16: Create Final Gate Run on Main
**Objective:** After all work is committed, run final gate on main to establish GO-CANDIDATE baseline.  
**Method:** Ensure main is merged with PR #825 → run gate with full production probe → capture scorecard  
**Success Criteria:** Gate scorecard shows GO-CANDIDATE status (all PASS)

### Priority 17: Document Final Gate Decision Criteria
**Objective:** Create comprehensive decision document showing how gate determines GO vs. NO-GO.  
**Method:** Document all 12+ gate conditions and decision logic  
**Success Criteria:** FINAL_GATE_DECISION_CRITERIA.md created

### Priority 18: Prepare Release Checklist
**Objective:** Create final release checklist for release manager/technical lead.  
**Method:** Extract all release requirements → create actionable checklist  
**Success Criteria:** RELEASE_CHECKLIST.md created with pre-release, release, post-release phases

### Priority 19: Create Final Authority Signoff Document
**Objective:** Create template for technical lead to sign off on release authority.  
**Method:** Combine all evidence (gate decision, P0 proof, inventory, production baseline) into signoff template  
**Success Criteria:** FINAL_AUTHORITY_SIGNOFF.md created with signature fields

### Priority 20: Commit All Stage 3-5 Evidence
**Objective:** Final commit containing all Stage 3-5 documentation and evidence.  
**Method:** Git add all new files → commit with comprehensive message → push to sprint branch  
**Success Criteria:** All evidence committed with auditable message

---

## EXECUTION APPROACH

Each priority will be executed with:
1. **Verification:** Check prerequisites and preconditions
2. **Implementation:** Execute the priority action
3. **Validation:** Verify output meets success criteria
4. **Commitment:** Document and commit evidence
5. **Reporting:** Report success or concerns

All work will maintain **100% accuracy and integrity** with no shortcuts or stubs.

---

## SUCCESS METRICS

- ✅ 990/990 inventory items classified (830 + 160 new)
- ✅ P0: 100% coverage verified
- ✅ P1: 100% coverage verified
- ✅ Final gate: GO-CANDIDATE status
- ✅ All evidence committed
- ✅ Authority signoff template ready

---

## NEXT: PROCEED WITH EXECUTION

Ready to execute all 20 priorities in sequence with full integrity assurance.

