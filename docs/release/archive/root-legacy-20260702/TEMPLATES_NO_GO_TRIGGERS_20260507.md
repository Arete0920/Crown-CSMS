# NO-GO TRIGGERS & POST-GATE MONITORING

**Pilot:** Crown 51x51 Deployment  
**Run Reference:** #270 / prod-deploy-20260507-orderfix-195608  
**Authority:** Operations Lead + Decision Authority  

---

## PURPOSE

After gate meeting approves GO, this document defines what events would REQUIRE immediate review and potential ROLLBACK.

If ANY of these occur, **STOP PILOT IMMEDIATELY** and convene emergency review.

---

## CRITICAL NO-GO TRIGGERS (IMMEDIATE ACTION REQUIRED)

### 1. Production Re-Deployment After Gate ❌ **INSTANT ROLLBACK**

**What:** Any new GitHub run deploys to production after gate meeting  
**Why:** Invalidates entire run #270 proof set  
**Action:** IMMEDIATELY ROLLBACK to pre-pilot state  
**Decision:** No review needed - rollback is mandatory  
**Who Decides:** Operations Lead has authority  

```
Test: Check GitHub Actions
  curl -s https://api.github.com/repos/[org]/[repo]/actions/runs \
    | grep -A5 "prod-deploy" | grep created_at

If ANY run after gate meeting timestamp → ROLLBACK TRIGGERED
```

---

### 2. Production Appsettings Change ❌ **INSTANT ROLLBACK**

**What:** BUILD_SHA, PROD_DEPLOY_TAG, or DEPLOY_RUN_ID changes  
**Why:** Means production code has been altered from proven state  
**Action:** IMMEDIATELY ROLLBACK  
**Decision:** No review needed - rollback is mandatory  
**Who Decides:** Operations Lead has authority  

```
Test: Hourly health check
  curl -s https://crown-api-prod.azurewebsites.net/api/health \
    | jq '.BUILD_SHA, .PROD_DEPLOY_TAG, .DEPLOY_RUN_ID'

If values differ from recorded values → ROLLBACK TRIGGERED
```

---

### 3. Automated Gate Falls Below 95 ❌ **ESCALATE TO DECISION AUTHORITY**

**What:** technical_runtime or evidence_freeze drop below 95  
**Why:** Means proof set is corrupted or invalid  
**Action:** STOP PILOT, escalate to Decision Authority  
**Decision:** Decision Authority must approve continuing or block  
**Timeline:** Must decide within 4 hours  

```
Test: Run scorecard
  ./scripts/release/39_run_95_plus_pilot_closure.ps1

If automated_minimum_lane_score < 95 → ESCALATE
```

---

### 4. Evidence File Corruption ❌ **INSTANT ROLLBACK**

**What:** Any of 6 evidence files fails SHA256 check  
**Why:** Proof integrity compromised  
**Action:** IMMEDIATELY ROLLBACK  
**Decision:** No review needed - rollback is mandatory  
**Who Decides:** Operations Lead has authority  

```
Test: Daily integrity check
  ./scripts/release/40_verify_evidence_immutable.ps1

If ANY file fails verification → ROLLBACK TRIGGERED
```

---

### 5. Security Incident Discovered ❌ **ESCALATE TO FOUNDER**

**What:** Any security breach, data exposure, or credential compromise  
**Why:** Pilot safety compromised  
**Action:** STOP PILOT, escalate immediately to Founder  
**Decision:** Founder decides whether to rollback or continue  
**Timeline:** Must decide within 1 hour  

**Examples:**
- Data breach discovered
- Unauthorized access detected
- Credential leakage found
- Ransomware/malware incident
- DDoS attack

```
Contact: Founder [CONTACT INFO]
  Message: "Security incident in pilot environment. Rollback triggered."
  Timeline: 1 hour decision required
```

---

### 6. Compliance Violation Discovered ❌ **ESCALATE TO COMPLIANCE OFFICER**

**What:** FERPA, COPPA, DPA, or contractual violation discovered  
**Why:** Legal/compliance risk exposed  
**Action:** STOP PILOT, escalate to Compliance Officer + Decision Authority  
**Decision:** Compliance Officer + Decision Authority together decide  
**Timeline:** Must decide within 4 hours  

**Examples:**
- Student data exported without authorization
- Parental consent requirements violated
- Data retention policy breached
- School district contract violated
- Accessibility requirement not met

```
Contact: Compliance Officer [CONTACT INFO]
  Message: "Compliance issue discovered in pilot. Review required."
  Decision needed: Can pilot continue or must rollback?
```

---

## OPERATIONAL NO-GO TRIGGERS (REVIEW & DECIDE)

### 7. Pilot Performance Degrades ⚠️ **DECIDE: CONTINUE OR ROLLBACK**

**What:** Error rate >5%, latency >2000ms, availability <99.5%  
**Why:** Pilot is harming user experience  
**Action:** Escalate to Operations Lead for decision  
**Decision:** Operations Lead decides: continue (with fixes) or rollback  
**Timeline:** Must decide within 24 hours  

---

### 8. Pilot Adoption Below Target ⚠️ **DECIDE: CONTINUE OR ROLLBACK**

**What:** Schools not activating pilot, teacher adoption <30%, student usage <20%  
**Why:** Pilot not reaching intended users  
**Action:** Escalate to Pilot Lead for decision  
**Decision:** Pilot Lead + Operations Lead: continue (extend timeline) or rollback  
**Timeline:** Must decide within 7 days  

---

### 9. Unexpected Resource Costs ⚠️ **DECIDE: CONTINUE OR ROLLBACK**

**What:** Azure/infrastructure costs exceed budget by >50%  
**Why:** Economic impact unsustainable  
**Action:** Escalate to Operations Lead + Decision Authority  
**Decision:** Operations Lead + Decision Authority: continue (optimize) or rollback  
**Timeline:** Must decide within 3 days  

---

### 10. Critical Bug Found ⚠️ **DECIDE: FIX OR ROLLBACK**

**What:** Blocking bug prevents core feature from working  
**Why:** Pilot cannot deliver value if core feature broken  
**Action:** Escalate to Technical Lead + Operations Lead  
**Decision:** Technical Lead estimates fix time, Operations Lead decides: fix or rollback  
**Timeline:** Must decide within 12 hours  

---

## MONITORING PROCEDURE

### Daily Health Checks (Automated)

```powershell
$script = "scripts/release/42_monitor_no_go_triggers.ps1"
.//$script  # Runs daily at 09:00, 14:00, 20:00 UTC
```

This script checks:
- ✓ Production appsettings unchanged
- ✓ Evidence files unchanged  
- ✓ No unauthorized deployments
- ✓ No security incidents
- ✓ Error rate <5%
- ✓ Availability >99.5%

### Manual Escalation

If ANY critical trigger detected outside of automation:

```
1. Stop pilot immediately (don't wait for scripted check)
2. Contact: Operations Lead + Decision Authority
3. Email subject: "PILOT NO-GO TRIGGER: [trigger name]"
4. Include: Evidence, logs, decision needed
5. Timeline: Depends on trigger (see above)
```

---

## POST-ROLLBACK PROCEDURE

If rollback is triggered:

1. **Operations Lead:** Execute rollback script
   ```powershell
   ./scripts/release/43_rollback_pilot_deployment.ps1
   ```

2. **Operations Lead:** Verify production restored to pre-pilot state
   ```powershell
   ./scripts/release/40_verify_evidence_immutable.ps1
   ```

3. **Decision Authority:** Notify all stakeholders of rollback
   - Schools: "Pilot has been suspended due to [reason]. Normal operations restored."
   - Support team: "Pilot is no longer active. Process inquiries normally."
   - Founder: Escalation complete, reason documented

4. **Decision Authority:** Schedule post-incident review (within 48 hours)
   - What went wrong?
   - How do we prevent this?
   - Can pilot restart with fixes?

---

## CONTACTS & ESCALATION

**Operations Lead:**  
Name: [TO BE ASSIGNED]  
Phone: [TO BE ASSIGNED]  
Email: [TO BE ASSIGNED]  
Backup: [TO BE ASSIGNED]  

**Decision Authority:**  
Name: [TO BE ASSIGNED]  
Phone: [TO BE ASSIGNED]  
Email: [TO BE ASSIGNED]  
Backup: [TO BE ASSIGNED]  

**Founder:**  
Name: [TO BE ASSIGNED]  
Phone: [TO BE ASSIGNED]  
Email: [TO BE ASSIGNED]  
After-hours: [TO BE ASSIGNED]  

**Compliance Officer:**  
Name: [TO BE ASSIGNED]  
Phone: [TO BE ASSIGNED]  
Email: [TO BE ASSIGNED]  
Backup: [TO BE ASSIGNED]  

---

## SIGN-OFF

Operations Lead (responsible for monitoring):  
Signature: ________________________ Date: ________

Decision Authority (responsible for decisions):  
Signature: ________________________ Date: ________

Founder (informed of triggers):  
Signature: ________________________ Date: ________

---

**This document is binding and becomes part of pilot governance.**  
**All contacts must acknowledge they have read and understand their role.**
