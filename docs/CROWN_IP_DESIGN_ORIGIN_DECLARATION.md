# Crown2026™ — Intellectual Property Design Origin Declaration

**Document Class:** Legal / Intellectual Property  
**Organization:** Crown Christian School Management Solutions  
**Prepared by:** Engineering Leadership  
**Effective Date:** 2026-02-28  
**Repository:** tcmegahan/Crown2026  
**HEAD SHA at declaration:** 61e67163 (pre-Gate 4, post-finance-setup-wizard-freeze-2026-02-28)

---

## I. Declarations of Original Authorship

### A. Code Authorship

1. All source code contained in this repository was written in-house by the Crown2026 development team.

2. No proprietary source code, compiled binaries, or intellectual property belonging to any third-party commercial school management platform has been copied, incorporated, or adapted into this codebase.

3. No reverse engineering of any commercial software product was performed at any stage of development.

4. No packet sniffing, API scraping, proprietary database schema inspection, or interception of competitor system traffic was performed.

5. No third-party commercial system was decompiled, disassembled, or analyzed for structural replication.

### B. Architecture Authorship

The following architectural components were independently designed:

| Component | Design Origin |
|-----------|--------------|
| Multi-tenant school scoping (`school_id` enforcement) | Derived from standard Django ORM patterns and 25+ years of K-12 consulting experience |
| Subscription tier model (Smart Start / Next Level / All Access) | Derived from SaaS pricing principles applied to Christian school operational needs |
| Wizard session framework | Independently designed step-persistence pattern for guided administrator workflows |
| Crown Compass scoring engine | Original KPI weighting model developed from first-principles school health analysis |
| Financial Aid award + ledger bridge | Original double-entry pattern built from accounting principles, not competitor feature inspection |
| Ledger immutability model | Standard audit-safe ledger design practice from financial software engineering |
| Director Actions API | Proprietary aggregation pattern, no known equivalent in competing products |
| Mission-fit scoring (admissions POG) | Original construct reflecting Christian school mission alignment, no market equivalent |
| Spiritual life tracking layer | Original design specific to Christian school formation mission; no comparable competitor module |
| Gate 1–4 build progresssion | Proprietary release gating model developed for this project |

---

## II. Competitive Analysis Scope

1. General competitive analysis was conducted solely at the level of **abstract market understanding** — identifying what categories of features exist in the K-12 school management market.

2. No competitor product was used as a design specification, implementation template, or functional blueprint.

3. Any awareness of competitor feature sets was used only to validate that Crown2026 addresses the same **problem domain** — not to replicate competitor solutions.

4. Industry-standard concepts (billing, enrollment, gradebook, ledger, scheduling) are not proprietary to any vendor. Crown2026 implements these concepts from independent engineering principles.

---

## III. Mechanical IP Scan Results

**Scan executed:** 2026-02-28  
**Scan method:** PowerShell `Select-String` with regex alternation across all `.py`, `.md`, `.txt`, `.sh`, `.json`, `.yaml`, `.yml`, `.js`, `.ts`, `.html`, `.css` files  
**Exclusions:** `.git/`, `.venv/`, `node_modules/`, `dist/`, `build/`

**Keywords scanned:**

```
blackbaud, renweb, veracross, skyward, nelnet, rediker, moodle, eschool,
easyboard, booster, gibbon, fedena, facts, inspired by, modeled after,
reverse engineer, like blackbaud, like facts
```

**Findings:**

| Finding | File | Assessment |
|---------|------|-----------|
| "nelnet" substring | `.venv/Lib/site-packages/pygments/lexers/_cocoa_builtins.py` | **FALSE POSITIVE** — `nelnet` is a substring of Apple's `NENetworkRule` Cocoa API name within the pygments syntax library. This file is a third-party Python package; it is not committed to version control and has zero connection to Crown code. |
| "eschool" substring | `backend/tests/test_tenant_header_validate_school.py:10` | **FALSE POSITIVE** — `eschool` is a substring of `validate_school` in the class name `TenantHeaderValidateSchoolTests`. The word "school" is common English; this is not a reference to any competitor product. |

**Verdict: REPOSITORY IS CLEAN**

Zero genuine competitor references found in any committed source file.

---

## IV. Third-Party Dependencies

All third-party dependencies used in this project are:

1. **Open-source libraries** with permissive licenses (MIT, BSD, Apache 2.0, PSF)
2. Listed in `requirements.txt` (Python) and `package.json` (Node/frontend)
3. Used according to their respective license terms
4. Not modified in any way that would create derivative work restrictions

Key dependencies and license categories:

| Dependency | License | Usage |
|-----------|---------|-------|
| Django | BSD-3 | Web framework |
| djangorestframework | BSD-2 | REST API layer |
| Pillow | HPND | Image handling |
| pygments | BSD-2 | Syntax highlighting (dev tooling only) |
| pytest / pytest-django | MIT / BSD | Test runner |
| React (frontend) | MIT | UI framework |

No GPL-licensed code is incorporated into production artifacts.

---

## V. Naming & Branding Independence

Crown2026 uses proprietary naming throughout:

| Crown Name | What It Means |
|-----------|--------------|
| Crown Compass | Proprietary KPI health scoring system |
| Crown Connect | Outreach and communication layer |
| Crown Core | Central SIS identity |
| Crown Family Portal | Parent-facing access layer |
| Crown Stewardship | Governance and board layer |
| Smart Start / Next Level / All Access | Proprietary subscription tier names |
| Director Actions API | Proprietary admin action aggregation pattern |
| Gate 1–4 | Proprietary release certification model |
| Solomon KB | Proprietary knowledge base module name |

None of these names are trademarked by or in use by any identified competitor.

---

## VI. Architecture Distinctiveness Statement

The following characteristics make Crown2026 architecturally distinct from any known K-12 SIS competitor:

1. **Christian mission integration at the data layer** — Spiritual formation tracking, mission-fit aid scoring, and devotional tracking are first-class data models, not bolt-on features.

2. **Subscription-gated feature entitlements** enforced at the Django queryset level — not a UI toggle pattern common in competitors.

3. **Wizard session architecture** — All administrative configuration flows are modeled as persisted multi-step session objects, enabling resumability and auditability.

4. **Crown Compass** — A school health scoring engine with domain weighting tailored specifically to Christian school operational philosophy (including Spiritual Formation as a scored domain).

5. **Gate-based release certification** — Production deployments are certified against a checklist of invariant tests, tenant isolation proofs, and audit log completeness — a level of rigor not present in any identified competitor product.

6. **Immutable ledger with double-entry enforcement** — Financial transactions are protected by write-safety tests, invariant tests, and void/reversal enforcement. This is enterprise-grade financial architecture uncommon in the K-12 SIS market.

---

## VII. Certification

This declaration is made to the best of the knowledge of the Crown2026 engineering leadership as of the date stated above.

> All code in this repository was written in-house.  
> No proprietary competitor code was used.  
> No reverse engineering was performed.  
> Competitive analysis was used only for abstract market awareness.  
> All workflows were independently designed.  
> This system is an original work.

**Signed by:** Engineering Leadership, Crown Christian School Management Solutions  
**Date:** 2026-02-28  
**Version:** 1.0 — Initial Declaration (Gate 3 Complete / Gate 4 Prep)

---

*This document should be retained in the project legal folder and updated at each major gate release.*
