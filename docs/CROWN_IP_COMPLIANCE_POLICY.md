# Crown2026™ — Developer IP Compliance Policy

**Document Class:** Engineering Policy / Developer Onboarding
**Effective Date:** 2026-02-28
**Owner:** Engineering Leadership
**Applies to:** All engineers, contractors, interns, and contributors to the Crown2026 repository

---

## Purpose

This policy exists to protect the intellectual property integrity of Crown2026 and ensure that every contribution to this codebase is defensibly original. Violations are a termination-level matter. This is non-negotiable.

---

## Rule 1: No Competitor Names in Code

**PROHIBITED:**
- Competitor brand names in any source file, commit message, branch name, comment, or variable
- Product names of any K-12 SIS, school billing, or education management platform
- References to specific competitor features by their vendor trade name

**Prohibited competitors (non-exhaustive):**

```
Blackbaud · FACTS Management · RenWeb · Veracross · Skyward
Alma · Rediker · eSchoolData · eSchoolPlus · Nelnet Campus Commerce
Moodle · Fedena · Gibbon · EasyBoard · Booster
```

**ALLOWED:**
- Generic industry terminology ("enrollment funnel", "gradebook", "ledger", "financial aid")
- Academic standard terminology (FERPA, FAFSA concepts, GAAP accounting concepts)
- Crown-specific proprietary names (Crown Compass, Director Actions API, Crown Connect, etc.)

---

## Rule 2: No Competitor References in Commits

**PROHIBITED commit messages:**

```bash
# NEVER DO THIS
git commit -m "add board dashboard like Blackbaud"
git commit -m "port the Veracross enrollment model"
git commit -m "our version of the FACTS billing wizard"
```

**REQUIRED commit style:**

```bash
# DO THIS
git commit -m "feat: board oversight metrics endpoint"
git commit -m "feat: enrollment wizard step persistence"
git commit -m "feat: billing wizard with installment validation"
```

If a commit message contains a competitor name, the branch will be rejected at code review.

---

## Rule 3: No Copying UI Screenshots into Design Files

- Do not import screenshots from competitor demos, marketing materials, or product tours into design files, Figma, or Notion
- Do not describe Crown UI in terms of "make it look like X but for Christians"
- UI design must start from Crown's mission, information architecture, and user roles — not from competitor wireframes

**Allowed:** General UI/UX pattern research from publicly available design system libraries (Material, Tailwind, etc.)
**Not allowed:** Layout replication from a specific competitor's interface

---

## Rule 4: No Proprietary Language Reuse

Internal documents, Slack messages, PRs, and code comments must not include:

- "like FACTS does it"
- "better than Blackbaud"
- "modeled after Alma"
- "our version of [product name]"
- "same as what [vendor] does"

**Use instead:**

> "Designed using industry best practices and 25+ years of K-12 consulting experience."

This is both accurate and legally defensible.

---

## Rule 5: No Reverse Engineering

**ABSOLUTELY PROHIBITED:**

- Packet sniffing competitor API traffic
- Inspecting competitor database schemas
- Decompiling competitor mobile apps or web bundles
- Screen-scraping competitor systems
- Using a competitor system as a test account to map feature behavior for replication

**Note:** Watching a competitor's **public marketing demo** is legally acceptable for market awareness. Systematically mapping that demo to build a functional replica is not.

If a feature idea came from a competitor demo:
- It must be rebuilt from first principles
- The implementation must reflect Crown's own data model and philosophy
- No code or schema may structurally mirror the competitor's implementation

---

## Rule 6: Original Naming Required

When building new features, use Crown's naming lexicon:

| Generic / Vendor-Style | Crown Alternative |
|-----------------------|-------------------|
| "Parent Hub" | Crown Family Portal |
| "Board Dashboard" | Crown Stewardship |
| "Booster campaign" | Crown Momentum |
| "EasyBoard pack" | Crown Board Pack |
| "SIS Portal" | Crown Core |
| "Compliance Dashboard" | Crown Integrity |
| "KPI Health" | Crown Compass |
| "Payment Gateway" | Crown Ledger |

When in doubt, ask before naming. Naming matters for trademark defensibility.

---

## Rule 7: Copyright Notice

All new Python modules must include this header at line 1:

```python
# Crown2026™
# Copyright (c) 2026 Crown Christian School Management Solutions
# All Rights Reserved.
```

All new React/TypeScript components must include:

```typescript
// Crown2026™
// Copyright (c) 2026 Crown Christian School Management Solutions
// All Rights Reserved.
```

This signals ownership and is required before Gate 4 Lock.

---

## Rule 8: Third-Party Dependencies

Before adding any new dependency:

1. Verify the license (MIT, BSD, Apache 2.0, or PSF are acceptable)
2. GPL-licensed packages are PROHIBITED in production code
3. All new dependencies must be added to `requirements.txt` or `package.json` with version pinning
4. Do not fork, patch, or modify open-source packages and include the modified version in this repo without legal review

---

## Mechanical Scan Requirement

At each Gate release, an IP scan must be run:

```powershell
# Run from repo root
$keywords = @(
  "blackbaud","renweb","veracross","skyward","nelnet","rediker",
  "moodle","eschool","easyboard","booster","gibbon","fedena","facts",
  "inspired by","modeled after","reverse engineer","like facts","like blackbaud"
)
Select-String -Recurse -Include "*.py","*.md","*.txt","*.sh","*.json","*.yaml","*.yml","*.js","*.ts" `
  -Pattern ($keywords -join "|") -CaseSensitive:$false 2>$null `
  | Where-Object { $_.Path -notmatch '\\.git' -and $_.Path -notmatch '\\.venv' -and $_.Path -notmatch '\\node_modules' }
```

Result must be documented in the gate certification archive.

**Known false positives (pre-cleared):**
- `nelnet` as substring of Apple `NENetworkRule` in `.venv/pygments` — not committed, not Crown code
- `eschool` as substring of `validate_school` in `test_tenant_header_validate_school.py` — English word "school", not a competitor reference

---

## Violation Policy

| Violation | Response |
|-----------|---------|
| Competitor name in source file (accidental) | Remove + amend commit |
| Competitor name in commit message | Rebase or note in PR + audit log |
| Copied UI structure from competitor screenshot | Designer review + redesign required |
| Evidence of reverse engineering | Immediate escalation to legal |
| Deliberate code replication from competitor | Termination |

---

## Onboarding Acknowledgment

Every engineer joining the Crown2026 project must:

1. Read this policy
2. Read the IP Design Origin Declaration (`docs/CROWN_IP_DESIGN_ORIGIN_DECLARATION.md`)
3. Confirm in writing (email or PR) that they understand and will comply

No access to the codebase is granted until acknowledgment is received.

---

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-02-28 | Initial policy — Gate 3 complete / Gate 4 prep |

---

*Questions? Escalate to Engineering Leadership before acting. When in doubt, stop and ask.*
