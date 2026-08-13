# CROWN Canonical Document Index

**Status:** Canonical documentation authority  
**Last verified:** 2026-08-13  
**Reviewed repository baseline:** `52ef87dbe6b4cb4c6ff147af11e386a519250a7e`

File ID means the Git blob SHA reviewed at the stated baseline. When a file changes, its row must be refreshed before final buyer delivery. Only listed documents may define current Crown-CSMS operating authority.

| Document | File ID reviewed | Purpose | Audience | Authority source | Owner | Last verified | Review cadence | Predecessor or superseded references |
|---|---|---|---|---|---|---|---|---|
| `README.md` | `3204c1eded01fdc80485b9f0ececa5e4bd708812` | Repository orientation and claim boundary | Owners, engineers, reviewers | This index; current release status | Founder/Product Owner | 2026-08-13 | Each authority or release change | Crown2026-certified-release wording |
| `docs/README.md` | `7dacd2a43cd91172b81d86deb0924d7d6a30dfb4` | Documentation navigation | All readers | This index | Documentation owner | 2026-08-13 | Quarterly; structure changes | Obsolete navigation pages |
| `docs/canonical/REPOSITORY_MANIFEST.md` | `8777883c702c52debabcf70e3f05b81133973582` | Allowed active repository surface | Maintainers, reviewers | This index | Repository owner | 2026-08-13 | Quarterly; structure changes | Generated or historical inventories |
| `docs/canonical/DILIGENCE_EVIDENCE_INDEX.md` | `4c2fe3db4335c2fe527bda984f7c6baba69b7262` | Diligence navigation and evidence boundary | Owners, buyers, reviewers | Current release status | Founder/Product Owner | 2026-08-13 | Each release/handoff decision | Crown2026 #1619 as Crown-CSMS authority |
| `docs/CURRENT_RELEASE_STATUS.md` | `4087cf7aaa5fcd7b8429db024a63d1e8ecf87e65` | Release, freeze, payment, and turnover posture | Owners, operators, buyers | Exact Crown-CSMS evidence; authorized human decision | Founder/Product Owner | 2026-08-13 | Every release-relevant change | Crown2026 status and #1619 |
| `docs/architecture/ARCHITECTURE_MAP.md` | `e1a5ee1591693a2682933b19f14ed51373555233` | Current architecture | Engineers, technical reviewers | Implemented source; decisions | Architecture owner | 2026-08-13 | Quarterly; architecture changes | Superseded architecture plans |
| `docs/architecture/DECISION_INDEX.md` | `17905c5dae3dc02a16ca125c8b3a26130eba63d4` | Architecture decision navigation | Engineers, reviewers | Approved decision records | Architecture owner | 2026-08-13 | Each architecture decision | Superseded decisions are historical |
| `docs/engineering/DEV_SETUP.md` | `b0c2de0a4e7a95b06a681ca0fdb89e25e895ffcb` | Reproducible engineering setup | Engineers | Current repository configuration | Engineering owner | 2026-08-13 | Each setup/dependency change | Machine-specific instructions |
| `docs/governance/CHANGE_MANAGEMENT.md` | `616a417b050e9e2f92929c458d3da0316895616a` | Change, evidence, approval, rollback policy | Maintainers, reviewers | Repository governance | Founder/Product Owner | 2026-08-13 | Quarterly; policy changes | Crown2026 #1619 control model |
| `docs/engineering/HUMAN_ACCOUNTABILITY_AND_DEVELOPMENT_ASSISTANCE_POLICY.md` | `1f41db405fcfa26be92bd26ee51280beffe74f95` | Human authority and assistance disclosure | Owners, contributors, reviewers | Founder/Product Owner policy | Founder/Product Owner | 2026-08-13 | Annual; policy changes | Tool-specific or unsupported approval wording |
| `docs/engineering/CONTRIBUTION_EVIDENCE_LEDGER.md` | `578ede740e0136989cf5bb9e41a12bc7307dd3da` | Evidence-backed attribution | Owners, contributors, diligence reviewers | Durable contribution evidence | Founder/Product Owner | 2026-08-13 | Each attribution change | Unsupported contributor claims |
| `docs/engineering/CODE_QUALITY_AND_PROVENANCE_STANDARD.md` | `b9e7098cbfe297dd8de01b985f63c9ddc069e282` | Quality and provenance controls | Engineers, reviewers | Repository governance | Engineering owner | 2026-08-13 | Quarterly | Obsolete audit guidance |
| `docs/operations/README.md` | `ba2fc84dbca53822e090482ec63e423db31be793` | Operations navigation | Operators, successor owner | Current operational controls | Operations owner | 2026-08-13 | Each operational change | Stale runbooks |
| `docs/ownership/OWNER_HANDOFF.md` | `e81397de861417bad6ca255193c0415c6ed152b4` | Controlled ownership transfer | Current and successor owners | Current release status; human acceptance | Founder/Product Owner | 2026-08-13 | Each handoff-stage change | Crown2026 #1619 handoff authority |
| `docs/KNOWN_LIMITATIONS.md` | `36ee5346531ece236ede605f03f90de09c683dc7` | Disclosed product/operational limits | Owners, buyers, operators | Verified evidence; accepted risk | Founder/Product Owner | 2026-08-13 | Each release/limitation change | Crown2026 limitation record |
| `SECURITY.md` | `78ce1e8b848804a2cf4f8552818815bc889750a5` | Security reporting and baseline | Users, engineers, security reviewers | Current security policy | Security owner | 2026-08-13 | Quarterly; security changes | Superseded security instructions |
| `CONTRIBUTING.md` | `9fe7048395ac58f47d8151a6d57b29bf0e0427cd` | Contribution requirements | Contributors | Change-management policy | Repository owner | 2026-08-13 | Quarterly; policy changes | Superseded contribution guidance |
| `AGENTS.md` | `a129a7d336127d5d23b230a9f906f915654aab35` | Repository work contract | Maintainers; repository tooling operators | Repository governance | Repository owner | 2026-08-13 | Each workflow/policy change | Prior assistant-specific operating rules |

## Classification and use

- **CURRENT/CANONICAL:** listed above and subject to its stated authority.
- **CONTROLLED SUPPORTING:** linked from a canonical record for a bounded purpose and noncontradictory.
- **HISTORICAL:** predecessor/provenance only; never current operating authority.
- **STALE/CONTRADICTORY:** conflicts with current authority; do not rely on it.
- **DUPLICATE:** repeats an authority without a defined supporting role.
- **UNSUPPORTED:** lacks exact evidence or authorized human decision.

Crown2026 and its issue #1619 are historical predecessor sources for Crown-CSMS. Issue #1619 must be refreshed before repeating any predecessor release claim, but it does not control a Crown-CSMS release.

## Buyer-safe hygiene rule

Active onboarding and buyer-facing material must be concise, current, nonduplicative, and vendor-neutral unless a named product is operationally material. Neutral wording must never obscure provenance or imply independent human review. Exclude copied conversations, generated proof dumps, obsolete completion boards, retired automation, unsupported marketing/transaction claims, and superseded status files from the active authority surface.
