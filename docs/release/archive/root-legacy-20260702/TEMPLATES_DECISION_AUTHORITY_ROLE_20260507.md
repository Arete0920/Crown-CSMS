# DECISION AUTHORITY ROLE DESCRIPTION

**Role:** Decision Authority for Crown 51x51 Pilot Gate  
**Scope:** Responsible for final GO/NO-GO decision on pilot deployment  
**Authority Level:** Executive - Can unilaterally block or approve pilot  

---

## RESPONSIBILITIES

1. **Review Evidence**
   - Review run #270 proof (SHA, tag, run_id)
   - Confirm production appsettings frozen
   - Verify all evidence files immutable
   - Review all human lane assessments (compliance, ops, founder)

2. **Governance Lane Assessment**
   - Is this pilot aligned with company policy?
   - Are there any governance blockers?
   - Score: 95+ or exception documented
   - **Note:** This is YOUR score - you own this lane

3. **Gate Meeting Authority**
   - Confirm all 4 decision-makers present
   - Ensure vote is unanimous (4/4 approve) or BLOCKED
   - Can request delay if not ready
   - Can call NO-GO unilaterally if unsafe

4. **Final Sign-Off**
   - Sign formal acceptance statement (locked to git)
   - Confirm acceptance of run #270 proof
   - Confirm understanding of rollback triggers

---

## ACCEPTANCE TEMPLATE

You must complete and sign this document at gate meeting:

```
DECISION AUTHORITY SIGN-OFF
Pilot: Crown 51x51 Deployment
Run: #270 | prod-deploy-20260507-orderfix-195608
Date: [GATE MEETING DATE]

I, _________________ (Print Name), acknowledge:

☐ I have reviewed run #270 proof (SHA, tag, run_id)
☐ I have reviewed all evidence files (6 total, immutable)
☐ I have reviewed production appsettings (frozen, verified)
☐ I have reviewed governance lane assessment (mine - at 95+ or exception noted)
☐ I have reviewed compliance lane (Compliance Officer certification)
☐ I have reviewed operations lane (Operations Lead certification)
☐ I have reviewed founder acceptance lane (Founder signature)
☐ I confirm all rollback triggers and procedures understood
☐ I accept responsibility for this deployment decision

MY DECISION: [ ] GO  [ ] NO-GO  (Circle one)

Reason for decision (if NO-GO):
__________________________________________________________________

Signature: ________________________    Date & Time: _______________
```

---

## ESCALATION PATH

If Decision Authority is unavailable:

1. **Escalation Contact:** [FOUNDER NAME] - Final authority
2. **Timeline:** If decision authority unavailable >24hrs, escalate to founder
3. **Interim:** No gate meeting can proceed without decision authority present

---

## WHAT YOU CANNOT DO

❌ Average scores across lanes (each lane is independent)  
❌ Approve pilot if ANY automated lane <95 (except with written exception)  
❌ Override founder if founder votes NO-GO  
❌ Change run #270 proof values (they're immutable)  
❌ Re-deploy production during gate meeting  

---

## WHAT SUCCESS LOOKS LIKE

✅ Gate meeting held with all 4 decision-makers present  
✅ All vote unanimously GO  
✅ Decision artifact signed and committed to git  
✅ Pilot launch authorization issued  

---

## CONTACT FOR QUESTIONS

**Pilot Program Lead:** [NAME - to be assigned]  
**Technical Lead:** [NAME - to be assigned]  
**Founder:** [NAME - to be assigned]  

**This is a binding commitment. Do not sign unless you fully understand the scope and risks.**
