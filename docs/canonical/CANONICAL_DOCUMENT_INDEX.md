# CROWN Canonical Document Index

**Status:** Canonical documentation authority  
**Last verified:** 2026-08-17

## Identity rule

The exact GitHub `main` commit being handed off is the repository source identity. This index no longer embeds a historical repository baseline or per-file blob IDs as if they remain current after later commits. Git history provides immutable file versions; current authority is the version of each canonical file contained in the exact `main` commit under review.

| Document | Purpose | Audience | Authority source | Owner | Review trigger |
|---|---|---|---|---|---|
| `README.md` | Repository orientation and claim boundary | Owners, engineers, reviewers | This index; current release status | Founder/Product Owner | Each authority or release change |
| `docs/README.md` | Documentation navigation | All readers | This index | Documentation owner | Structure changes |
| `docs/canonical/REPOSITORY_MANIFEST.md` | Allowed active repository surface | Maintainers, reviewers | This index | Repository owner | Structure changes |
| `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md` | Diligence navigation and evidence boundary | Owners, buyers, reviewers | Current release status | Founder/Product Owner | Each handoff decision |
| `docs/CURRENT_RELEASE_STATUS.md` | Release, freeze, payment, and turnover posture | Owners, operators, buyers | Exact Crown-CSMS evidence; authorized owner decision | Founder/Product Owner | Every release-relevant change |
| `docs/architecture/ARCHITECTURE_MAP.md` | Current architecture | Engineers, technical reviewers | Implemented source; decisions | Architecture owner | Architecture changes |
| `docs/architecture/DECISION_INDEX.md` | Architecture decision navigation | Engineers, reviewers | Approved decision records | Architecture owner | Each architecture decision |
| `docs/engineering/DEV_SETUP.md` | Reproducible engineering setup | Engineers | Current repository configuration | Engineering owner | Setup/dependency change |
| `docs/governance/CHANGE_MANAGEMENT.md` | Change, evidence, approval, rollback policy | Maintainers, reviewers | Repository governance | Founder/Product Owner | Policy change |
| `docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md` | Human authority and assistance disclosure | Owners, contributors, reviewers | Founder/Product Owner policy | Founder/Product Owner | Policy change |
| `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md` | Evidence-backed attribution | Owners, contributors, diligence reviewers | Durable contribution evidence | Founder/Product Owner | Attribution change |
| `docs/engineering/CODE_QUALITY_AND_PROVENANCE_STANDARD.md` | Quality and provenance controls | Engineers, reviewers | Repository governance | Engineering owner | Quality-policy change |
| `docs/operations/README.md` | Operations navigation | Operators, successor owner | Current operational controls | Operations owner | Operational change |
| `docs/ownership/OWNER_HANDOFF.md` | Controlled ownership transfer | Current and successor owners | Current release status; owner/successor acceptance | Founder/Product Owner | Handoff-stage change |
| `docs/KNOWN_LIMITATIONS.md` | Disclosed product/operational limits | Owners, buyers, operators | Verified evidence; accepted risk | Founder/Product Owner | Limitation/release change |
| `SECURITY.md` | Security reporting and baseline | Users, engineers, security reviewers | Current security policy | Security owner | Security-policy change |
| `CONTRIBUTING.md` | Contribution requirements | Contributors | Change-management policy | Repository owner | Contribution-policy change |
| `AGENTS.md` | Repository work contract | Maintainers; repository tooling operators | Repository governance | Repository owner | Workflow/policy change |

## Classification and use

- **CURRENT/CANONICAL:** listed above as contained in the exact current `main` commit.
- **CONTROLLED SUPPORTING:** linked from a canonical record for a bounded purpose and noncontradictory.
- **HISTORICAL:** predecessor/provenance only; never current operating authority.
- **STALE/CONTRADICTORY:** conflicts with current authority; do not rely on it.
- **DUPLICATE:** repeats an authority without a defined supporting role.
- **UNSUPPORTED:** lacks exact evidence or authorized owner decision.

Crown2026 and its issue #1619 are historical predecessor sources for Crown-CSMS. They do not control Crown-CSMS release or turnover.

## Buyer-safe hygiene rule

Active onboarding and owner-facing material must be concise, current, nonduplicative, and vendor-neutral unless a named product is operationally material. Neutral wording must never obscure provenance or imply independent human review. Exclude copied conversations, generated proof dumps, obsolete completion boards, retired automation, unsupported marketing/transaction claims, and superseded status files from the active authority surface.
