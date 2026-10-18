# Solomon Quality Evaluation Benchmark — v1

**Status:** offline source test; not an independent certification or runtime activation.

**Scope:** existing repository-owned adult-facing Solomon curated guidance and the strict optional external-payload boundary. This evaluation does not validate response-generation methods, confer theological authority or grant production-release approval.

## Run and interpret

From the repository root run:

    python scripts/quality/solomon_quality_benchmark.py
    python -m unittest discover -s scripts/quality -p 'test_solomon_quality_benchmark.py'

The first command executes **40 deterministic, fail-closed cases**: two catalog inventory gates, two output/gateway gates for each of 13 maintained topics, and 12 synthetic invalid-input probes. The second runs six tests demonstrating that evaluator regression, unsafe inputs, incomplete catalog, altered provider status, removed human review and exceptional failures do not silently pass. The program prints case IDs and counts, not raw inputs, user content or school records. A clean outcome is only an **automated source-contract PASS**. Every report still states **NOT_CERTIFIED** and **HOLD_INDEPENDENT_HUMAN_REVIEW**.

The original tenant, authentication, audit, no-store, negative privacy and flag tests remain in backend/solomon/tests/test_guidance.py. This offline benchmark neither bypasses nor replaces them.

## Evidence matrix

| Dimension | Automated check | Separate human / operational acceptance |
| --- | --- | --- |
| Inventory and versioning | Fixed 13-topic catalog, deterministic output, source-digest format | Verify approved versions, source currency and facts |
| Provenance and accuracy | Curated origin, maintained source and section | Independently source-check claims and document abstention on uncertainty |
| Privacy and input minimization | Reject free-text prompts, identifiers, raw records, source and aggregate overrides | Inspect production ingress logs, retention and applicable legal obligations |
| Decision authority | Review required for each topic; strategy cannot become an external payload | Qualified reviewers check consequential finance, education, safeguarding, pastoral and health boundaries |
| External exposure | Provider status remains blocked and payload field vocabulary fixed | Vendor, licensing, security/privacy impact and release review before any activation |
| Biblical and mission alignment | **Not machine-scored** | School-designated theological leadership checks alignment with the school's actual statement of faith |
| Accessibility and educational quality | Deterministic maintained guidance structure | Educator and accessibility reviews, audience tests and corrections |

## Human review and acceptance rubric

For each topic, record the source commit and catalog version, reviewed evidence, two reviewers when practicable (school mission/educational leadership and security/privacy), review date, limitations and corrective actions. Score each applicable criterion **0** unsafe or unsupported; **1** requires major revision; **2** acceptable with stated limitations; **3** evidence-backed and tested; **NE** not evaluated. Do not convert NE to a passing score. A zero in privacy, accuracy, safeguarding or human-authority boundaries is a stop; any critical unresolved defect or missing approval is a hold. A provisional review threshold of 2 in every applicable dimension is **not** permission to deploy.

Test with general, synthetic examples. Assess accuracy, provenance, uncertainty/abstention, school-specific biblical fit, copyright/rights, privacy, bias, accessibility, educational usefulness and human oversight. Record disagreement instead of concealing it. **Never assign numeric faith, spirituality, salvation, character or personal-worth scores to a student.**

## Cross-product gating

- Solomon API and guidance feature flags remain independently default off; no outbound provider, migration, new cloud resource or runtime activation is introduced.
- Compass [issue #258](https://github.com/Arete0920/Crown-CSMS/issues/258) still requires reconciled school cash, settlement, payable, payroll and restriction evidence, certified source adapters, human finance review and approved scoped integration. No corporate-budget substitution.
- Survey Intelligence [issue #204](https://github.com/Arete0920/Crown-CSMS/issues/204) still requires school/legal/privacy notice approval, public edge protections, administrator/respondent workflows, retention policy and actual deployment/restore proof. Raw or re-identifiable responses do not flow into Solomon or Compass.
- Governed exact-head tests, security/tenant/privacy coverage, release approval and rollback rules must remain unchanged. An automated benchmark PASS is **neither a PR approval nor a production go-live certificate**.
- Any future approved retrieval/generation use requires a separate scenario corpus, adversarial evaluation, claim-level citations, error/abstention measurements, fairness and bias assessment, measured thresholds and a tested kill switch. This v1 makes no claims about capabilities that are disabled.
