# CROWN Solo Developer Approved Workaround

Status: Governance control document  
Scope: Crown2026 review, approval, release, and deployment controls  
Purpose: Preserve segregation of duties when Crown2026 is operated by a solo developer/product owner.

## 1. Mandatory Rule

The solo developer/product owner cannot serve as the independent reviewer or approver for work they authored, directed, implemented, or materially shaped.

This rule applies to:

- code changes,
- workflow changes,
- deployment changes,
- security or tenant-isolation changes,
- release readiness decisions,
- Azure staging or production deployment decisions.

## 2. Approved Workaround

When an independent human reviewer is not immediately available, Crown uses the approved solo-developer workaround:

1. ChatGPT acts as support, architect, engineering reviewer, and evidence auditor.
2. ChatGPT does not act as the independent human approval authority.
3. GitHub connector is used as the primary source of repository truth.
4. GitHub Actions, required checks, branch rules, PR evidence, and deployment evidence provide the control path.
5. The work remains draft, NO-GO, or blocked until the required evidence packet is complete.
6. The final packet must state which control path was used:
   - independent human reviewer,
   - required GitHub rule/check,
   - CI and release gate evidence,
   - or solo-developer approved workaround.
7. The product owner may accept business intent, priority, and product direction, but must not be recorded as the independent technical reviewer for their own work.

## 3. Evidence Bar

This workaround does not lower the evidence standard.

It raises the documentation requirement because the lack of an independent human reviewer must be offset by stricter proof:

- current branch verified,
- commit SHA verified,
- changed files reviewed,
- tests/checks reviewed,
- deployment target verified when applicable,
- post-deployment evidence captured when applicable,
- risks explicitly listed,
- PASS / NO-GO / BLOCKED decision recorded.

## 4. Required Packet Language

Use this language in relevant PR, release, or deployment packets:

```text
Segregation of duties:
The product owner is the solo developer and cannot self-review or self-approve this work.

Control path used:
[Independent reviewer / GitHub required checks / CI release gate / Solo-developer approved workaround]

ChatGPT role:
Support, architecture, engineering review, and evidence audit only. Not independent human approval authority.
```

## 5. Deployment Rule

For Azure deployment, the deployment packet must identify the control path before deployment is treated as PASS.

If the control path is missing, the decision is NO-GO.
