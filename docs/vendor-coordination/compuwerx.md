# CompuWerx Integration Status

Status: quarantined pending vendor coordination.

CROWN is not currently claiming CompuWerx production readiness, payment-provider readiness, webhook readiness, dispute workflow readiness, payout reconciliation readiness, or sandbox readiness.

Reason for quarantine:
- Prior repo state contained multiple CompuWerx-related runtime and documentation surfaces.
- Current work should avoid exposing or certifying CompuWerx behavior until implementation details are coordinated with CompuWerx developers.
- The intended future integration contract, webhook verification model, tenant behavior, payment-state mutation rules, and reconciliation workflow must be confirmed before restoration.

Restoration criteria:
1. Vendor implementation requirements documented.
2. Webhook trust model confirmed.
3. Signed request verification proven.
4. Unsigned and invalid signature requests denied.
5. Payment-state mutation rules proven by tests.
6. Tenant and permission boundaries proven.
7. Frontend surfaces restored only after backend contract is validated.
8. Release evidence updated without production-readiness overstatement.