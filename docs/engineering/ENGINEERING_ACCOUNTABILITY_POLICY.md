# Engineering Accountability Policy

**Status:** Canonical engineering governance
**Owner:** TC Megahan, Founder/Product Owner

## Authority

TC Megahan created CROWN and serves as Founder/Product Owner and repository owner. Product architecture, workflow rules, business requirements, acceptance decisions, and release authority remain human-controlled responsibilities.

Specific contributor credit is based on durable repository evidence. Historical involvement must not be converted into unsupported claims about specific implementation, review, or approval work.

## Engineering controls

CROWN engineering uses conventional software-development controls, including:

- written requirements and architecture decisions;
- bounded pull requests and line-by-line diff review;
- unit, integration, contract, and browser tests;
- static analysis and code-quality checks;
- dependency, license, and vulnerability scanning;
- tenant-isolation and authorization verification;
- migration and schema-governance checks;
- exact-head CI evidence before release decisions;
- documented rollback and recovery procedures.

## Accountability

- Human owners are accountable for scope, correctness, security, verification, acceptance, and release decisions.
- CI and test results are technical evidence and do not substitute for required human approval.
- Precise contribution claims require durable evidence.
- Do not manufacture attribution, infer authorship from style, or convert an unverified status into a definitive external claim.
- The repository owner cannot represent self-review as independent review where independent review is specifically required.

## Pull-request expectations

Non-trivial pull requests record the human owner, evidence-backed contributors, verification performed, unresolved findings, exact head identity, and rollback action. Changes merge only after applicable release and security gates are satisfied.
