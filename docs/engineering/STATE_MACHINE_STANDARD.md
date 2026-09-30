# Crown State-Machine Standard

Business workflows with lifecycle status must define legal transitions, terminal states, actor authority, side effects, and idempotency behavior.

## Required properties

1. Unknown status strings are rejected.
2. A transition cannot silently skip required contractual, financial, or review prerequisites.
3. Terminal states cannot be reopened except through an explicit authorized transition.
4. Side effects are attached to transitions through idempotent services.
5. Transition attempts produce audit evidence when the domain is consequential.
6. Dashboards consume state; they do not invent or overwrite it.

## Priority domains

Admissions/enrollment, re-enrollment, financial aid, payment/refund/dispute, communications outbox, surveys, onboarding, discipline/student care, CrownPass redemption, and provisioning.

Existing domain-specific transition contracts remain authoritative. This standard defines the cross-domain minimum.
