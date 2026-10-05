# Solomon OpenAI implementation and release review

Reviewed October 5, 2026. Owner selected OpenAI. Status: optional provider adapter
implemented; production activation and account-specific contractual clearance pending.
This is an engineering contract review, not legal certification or contract execution.

## Implementation boundary

The curated endpoint remains independent of external generation.
`POST /api/solomon/assistance/` shares its tenant, adult-role, JSON-only,
acknowledgement, throttle and audit boundaries. It additionally excludes strategy.
Only the maintained generic title, guidance, checklist and template leave CROWN.
No tenant identifier, user identifier, school records, metrics, recipient list or
submitted free text enters the provider request. No external retrieval, files,
tools, conversation history or operational writes are available.

The adapter uses the fixed HTTPS Responses endpoint, verified TLS, no redirects,
no ambient proxies, no automatic retries, connect/read timeouts of 3/10 seconds,
a 16 KiB request bound, 64 KiB response bound and 1,024 output-token cap.
Read timeout is an inactivity limit, not a guaranteed absolute completion deadline.
Strict JSON schema and local shape/length checks reject incomplete, refused,
tool-containing or malformed output. These checks do not verify truth, fairness,
translation accuracy or semantic adherence. Every result remains a human-reviewed
draft linked to the maintained source and rendered as plain text.

A durable requested audit precedes generation. Completion records mode,
source/release fingerprints and an output digest; raw prompts, outputs and secrets
are excluded. Requested audit does not prove a provider call occurred. Audit
failure withholds output; failure after a call cannot reverse its cost.
Existing audit access/retention rules and infrastructure logging require runtime review.

A TLS Redis atomic UTC-day project quota is mandatory across replicas. Quota
failure/exhaustion prevents a call. Reservations are never refunded because a
timeout may still incur cost. This is a request cap, not a dollar guarantee.
Keep the namespace stable across replicas and releases; changing it resets the
counter. Configure a separate project spending control and monitor usage.
Provider, quota or release failures return honestly labeled curated guidance.
The frontend offers Draft with AI only behind its separate default-off flag;
closing a dialog cancels display, not guaranteed provider processing or billing.

## Agreements and current terms

Do not put signed contracts, private review evidence, billing details or keys in
this public repository. Confirm the actual contracting entity and accepted version
in the account before activation. An environment reference is an operator
acknowledgement, not proof of legal review, consent or an executed agreement.

| Source and version | Review conclusion and action |
| --- | --- |
| [OpenAI Services Agreement](https://openai.com/policies/services-agreement/), effective January 1, 2026 | Section 2.2 permits API integration in customer applications; separate permission from ChatGPT is unnecessary. Customer remains responsible for input rights, output use and end users. Output ownership between the parties does not guarantee uniqueness or third-party clearance. Confirm entity, acceptance, fees, suspension/termination, liability limits, indemnity exclusions and dispute terms against CROWN's obligations. No blanket school-law compliance warranty is inferred. |
| [Data Processing Addendum](https://openai.com/policies/data-processing-addendum/), effective January 1, 2026 | Incorporated for personal-data processing under the agreement. Review controller/processor roles, lawful instructions, transfers, security, deletion/return exceptions and subprocessor consent. Breach notification is without undue delay; do not promise a fixed notification period. Subprocessor changes allow a 30-day objection process. Compare these commitments with school contracts. |
| [Service Terms](https://openai.com/policies/service-terms/), updated September 29, 2026 | Additional API, beta and indemnity provisions apply. Output indemnity has exclusions; beta services have different protections. Generated code can carry third-party licenses. Select an eligible production model and review its terms; this change pins no default model or beta. |
| [Usage Policies](https://openai.com/policies/usage-policies/), effective October 29, 2025 | Preserve restrictions on harmful uses, sensitive profiling and high-stakes decisions. This feature does not automate admissions, grading, discipline, aid, health or pastoral decisions. It does not infer emotions or profile students. Human review remains mandatory. |
| [API data controls](https://developers.openai.com/api/docs/guides/your-data), reviewed October 5, 2026 | API content is not used for training by default unless opted in. Abuse monitoring can retain content up to 30 days, with exceptions. Responses application state depends on settings; this adapter sets store, background and stream false. Store false is not Zero Data Retention. ZDR/Modified Abuse Monitoring require eligibility and approval; model, caching and safety exceptions need account-specific review. Do not claim zero retention or broader absence of secondary processing. |
| [Subprocessor list](https://openai.com/policies/sub-processor-list/), updated July 9, 2026 | Multiple vendors and processing geographies are involved. Review the complete current list and transfer terms; do not claim OpenAI-only processing or US-only residency. Reconcile vendor restrictions in CROWN and school agreements. |
| [Security measures](https://cdn.openai.com/osa/security-measures.pdf) and [Privacy Policy](https://openai.com/policies/privacy-policy/) | Review contractual controls and account-data handling. Vendor statements are not an independent audit of CROWN. Obtain authorized assurance evidence privately where required. The privacy policy does not replace the DPA. |
| [Service Credit Terms](https://openai.com/policies/service-credit-terms/) | Review purchased-credit conditions, expiration and refund limits before funding. No credits or paid requests were purchased in this implementation. |
| [Sharing and publication policy](https://openai.com/policies/sharing-publication-policy/) | Review applicable publication/disclosure requirements before distributing drafts. The UI identifies model-generated drafts and requires human review; it does not publish them. |

Health information is prohibited. A Healthcare Addendum and eligible services would
be needed for any separately authorized PHI expansion; no such expansion is approved.
FERPA, COPPA, state student/consumer privacy laws, accessibility, discrimination,
notice/consent and school-specific duties remain deployment-specific legal review.
See [the existing privacy boundary](SOLOMON_AI_PRIVACY_BOUNDARY.md).
Generic-only requests reduce exposure but do not settle platform-wide obligations.

## Required private release evidence and configuration

All flags default false; credentials, model, quota namespace and review references
default empty, and the daily cap defaults zero. There is no configured live model.

| Setting | Required evidence or value |
| --- | --- |
| `CROWN_SOLOMON_API_ENABLED`, `CROWN_SOLOMON_GUIDANCE_ENABLED` | Existing authenticated curated guidance gates |
| `CROWN_SOLOMON_EXTERNAL_ENABLED` | External kill switch, enabled only for an approved release |
| `CROWN_SOLOMON_RELEASE_APPROVED` | Accountable release authority after all private evidence is complete |
| `OPENAI_API_KEY` | Restricted server-side project secret through the authorized secure setup flow |
| `CROWN_SOLOMON_MODEL` | Explicit eligible model, evaluated against this exact catalog and policy |
| `CROWN_SOLOMON_QUOTA_REDIS_URL` | Private TLS Redis URL without query/fragment, verified certificates |
| `CROWN_SOLOMON_QUOTA_NAMESPACE` | Stable project identifier shared by all replicas |
| `CROWN_SOLOMON_DAILY_REQUEST_LIMIT` | Approved integer from 1 to 1,000 and separate spending controls |
| `CROWN_SOLOMON_CONTRACT_REVIEW_REF` | Private accepted-contract/entity and jurisdiction review |
| `CROWN_SOLOMON_RETENTION_REVIEW_REF` | Verified project training, retention, model eligibility, subprocessors and geography |
| `CROWN_SOLOMON_EVALUATION_REVIEW_REF` | Synthetic live evaluation: factuality, refusal, boundary adherence, accessibility and failure cases |
| `CROWN_SOLOMON_BUDGET_REVIEW_REF` | Pricing, quota, spending enforcement, alerts and accountable owner |
| `CROWN_SOLOMON_CORPUS_REVIEW_REF` | Rights and privacy clearance of all maintained sources |
| `CROWN_SOLOMON_RELEASE_FINGERPRINT` | Reviewed value from `solomon.provider.release_fingerprint(model, daily_limit)` |
| `VITE_SOLOMON_GUIDANCE_ENABLED`, `VITE_SOLOMON_EXTERNAL_ENABLED` | Separately approved frontend build flags; backend remains authoritative |

The fingerprint binds model, daily cap, catalog contents, policy versions,
instructions, endpoint, token cap and output schema. Changes invalidate the
configured fingerprint and close generation until reevaluated. It is not a
signature or independent compliance proof.

Use separate staging/production projects; never expose a key in browser code,
chat, tests, repository or public evidence. Review [production guidance](https://developers.openai.com/api/docs/guides/production-best-practices).
Account-target lookup did not complete. No key was created, contract accepted,
billing configured, retention verified, real model evaluated or paid API call made.

## Verification and rollback

Synthetic tests cover exact input, tenant/role exclusion, release gates and
fingerprint drift, TLS quota, fixed transport, malformed/refused output, fallback
and audit failures. UI tests cover explicit acknowledgement, labels, plain text,
source validation and late-response cancellation. Browser smoke uses synthetic
stubs and does not certify a live provider or deployed environment.
Run the repository's required exact-head CI before merging. Pending local tests
were interrupted by an execution-environment disconnect; do not cite them as passed.

Production closure requires private evidence above plus deployed authentication,
logging, quota, spending enforcement and smoke validation. Disable
`CROWN_SOLOMON_EXTERNAL_ENABLED` for immediate external rollback; curated help
continues under its existing gate. No migration, payment workflow or automatic
communication is introduced.
