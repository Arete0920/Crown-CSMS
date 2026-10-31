# CROWN Microsoft Entra Immutable Identity Binding

**Status:** source hardening candidate; no production Microsoft tenant is certified by this document.

## Security authority

CROWN Microsoft bearer authentication uses Microsoft Entra's immutable identifiers:

- `tid` — the Entra tenant/directory identifier.
- `oid` — the object identifier for the user in that tenant.

Mutable values such as email, `preferred_username`, UPN display values, names, and
Microsoft application-role claims are not CROWN identity or authorization authority.

CROWN roles remain CROWN-owned `UserRole` records. A Microsoft token never creates,
changes, or removes CROWN roles.

## Data model

### MicrosoftTenantBinding

A binding connects a CROWN school to one Entra tenant ID.

Multiple schools may intentionally bind to the same tenant, which supports diocesan
or other shared Microsoft tenants without treating the tenant ID as a school ID.

### MicrosoftIdentityLink

A link connects one CROWN user to one immutable Entra `oid` through a school tenant
binding.

Within one binding:

- an `oid` maps to only one CROWN user;
- a CROWN user maps to only one `oid`;
- the CROWN user must belong to the bound school directly or through a persisted
  school role.

If the same `tid` + `oid` is represented through more than one school binding,
all active links must resolve to the same CROWN user. Conflicting mappings fail
authentication.

## Provisioning

Provisioning is explicit. The bearer-token authentication path does not create
users or links.

Use the Django administration interface under **Integrations**:

1. Create a Microsoft tenant binding for the school using the exact Entra tenant
   GUID.
2. Create an identity link using the exact Entra user object GUID and an existing
   CROWN user.
3. Verify the CROWN user belongs to the same school directly or through
   `UserRole`.
4. Verify both records are active.
5. Preserve the resulting CROWN audit events.

After creation, the school/tenant identity and user/object identity fields are
read-only in Django admin. Deactivation is the supported access-revocation control;
do not repurpose an existing immutable binding for another tenant or person.

## Authentication behavior

A Microsoft bearer token must first pass the existing signature, audience, issuer,
expiration, and configured-tenant validation. CROWN then requires valid GUID
`tid` and `oid` claims and resolves only active persisted identity links.

Authentication fails closed when:

- `tid` or `oid` is missing or malformed;
- no active binding exists;
- the linked CROWN user is inactive;
- the link has no active CROWN school membership;
- one `tid` + `oid` resolves to conflicting CROWN users.

Changing a user's Microsoft email/UPN does not change the CROWN identity link.

## Recovery

If a mapping is wrong:

1. deactivate the incorrect identity link;
2. preserve the audit record and the incorrect identifiers for investigation;
3. create the correct binding/link as a new immutable mapping;
4. verify CROWN school membership;
5. test authentication with a non-production or specifically authorized account;
6. only then retire obsolete inactive records according to retention policy.

Do not recover by enabling email-based matching or token-role assignment.

## Acceptance

Source hardening is complete only when repository migration, backend, tenant,
security, and policy gates pass on the exact PR head.

Provider/runtime acceptance remains separate and requires an authorized Microsoft
Education tenant test proving:

- a provisioned `tid` + `oid` authenticates the intended CROWN user;
- a changed UPN/email still authenticates the same CROWN user;
- an unprovisioned `oid` is rejected;
- a disabled CROWN link is rejected;
- a conflicting mapping is rejected;
- Microsoft token roles do not alter CROWN role grants;
- cross-school tenant denial remains unchanged.
