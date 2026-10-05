# CROWN Electronic Forms & Signatures

## Purpose

CROWN provides a provider-neutral electronic forms and signature subsystem for school agreements, permissions, acknowledgments, contracts, and other records that require attributable consent or signature evidence.

This subsystem is intentionally separate from any third-party vendor. The native implementation is the default provider. A future external provider may be added behind the provider interface without changing CROWN's canonical envelope, signer, document-hash, or audit-evidence model.

## Canonical records

- `ElectronicFormTemplate` — school-scoped, versioned form definition.
- `ElectronicEnvelope` — immutable retained snapshot of the exact form and populated data issued for signature.
- `ElectronicSigner` — explicitly assigned authenticated signer.
- `ElectronicSignatureEvidence` — append-only consent, withdrawal, paper-copy, and signature evidence.

The envelope snapshot and SHA-256 digest are CROWN's canonical evidence of the exact record presented for signature. Template versions are immutable; amendments require a new template version and new envelope.

## Signing controls

CROWN native signing requires all of the following:

1. authenticated user identity;
2. explicit assignment of that user to the envelope;
3. same-school tenant scope;
4. successful hash verification of the retained document snapshot;
5. current electronic-record consent;
6. acknowledgement that the signer can access and retain the record;
7. explicit intent to sign;
8. typed signer name;
9. append-only timestamped evidence tied to the exact document hash.

An envelope is not marked complete until every assigned signer has completed the signature step.

## Electronic-record consent and paper path

The system exposes a versioned consent disclosure and records the exact disclosure version accepted by the signer. The native baseline includes:

- consent to electronic records/signatures;
- no-fee paper copy option;
- ability to withdraw electronic consent before signing;
- acknowledgement of browser/device requirements for access and retention;
- retained readback of the exact signed record.

Schools remain responsible for approving their final disclosure wording, paper-process contact details, and any state- or transaction-specific requirements.

## Legal baseline and limits

The implementation is designed around the federal E-SIGN Act and state electronic-transactions principles, including agreement to transact electronically, signer attribution, intent, record retention, accessibility, and reproducibility.

This architecture is an engineering control, not legal advice. Electronic-signature validity can depend on the transaction type, governing law, school policy, consumer-disclosure requirements, notarization requirements, age/capacity, and other facts. Counsel should review production templates and any transaction-specific requirements before broad use.

## Privacy and security

- No public anonymous signing is enabled in this foundation.
- Native signing requires an authenticated CROWN account assigned to the envelope.
- Cross-school access fails closed.
- Raw provider secrets are not stored in envelope records.
- Evidence is append-only and protected from hard deletion through the application model.
- The retained document is returned only to an assigned signer or a user with `forms.manage` in that school.
- External provider activation is not implied by this subsystem.

## Provider abstraction

`electronic_forms.providers.SignatureProvider` defines the provider boundary.

The initial provider is `crown_native`, which performs no external network call. A future provider adapter must preserve:

- canonical CROWN envelope identity;
- document hash parity;
- signer mapping;
- status reconciliation;
- webhook authentication and idempotency;
- audit evidence;
- retention/export requirements;
- fail-closed behavior when provider state is ambiguous.

External provider identifiers may be stored in `external_reference`, but CROWN remains the canonical school record.

## Initial API

- `GET /api/v1/forms/consent-disclosure/`
- `GET|POST /api/v1/forms/templates/`
- `POST /api/v1/forms/envelopes/`
- `GET /api/v1/forms/envelopes/my/`
- `GET /api/v1/forms/envelopes/<id>/`
- `POST /api/v1/forms/envelopes/<id>/consent/`
- `POST /api/v1/forms/envelopes/<id>/sign/`
- `POST /api/v1/forms/envelopes/<id>/withdraw-consent/`
- `POST /api/v1/forms/envelopes/<id>/paper-copy/`

## Production boundaries

This foundation does **not** yet claim:

- remote identity proofing beyond authenticated CROWN identity;
- notarization;
- witness workflows;
- SMS/email signing links;
- external provider delivery;
- PDF visual signature placement;
- qualified or advanced electronic-signature regimes outside ordinary U.S. school transactions;
- legal sufficiency for every form type or jurisdiction.

Those capabilities require separate design, security, legal, and release evidence.
