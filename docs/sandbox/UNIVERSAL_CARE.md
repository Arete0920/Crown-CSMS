# Isolated local presenter care fixtures

This source increment reuses the existing fictional hosted-buyer entitlement and
Daycare fixture implementations and the existing local Heritage Camp generator.
Original Heritage and prospect workspaces retain their existing authorization.
It is not hosted activation authority or five-module release certification.

After preparing the isolated presenter described in UNIVERSAL_PRESENTER.md:

```sh
python manage.py prepare_universal_care
python manage.py prepare_universal_care --apply
```

Default preflight is read-only. Apply creates a school-specific seven-day
fictional care plan, disabled payment provider, Daycare site/room/child, fictional
custody/staff assertions, and zero-priced AM/PM enrollments for the already
verified Reed learner. Every policy/qualification assertion is explicitly
fictional. No real licensing, custody or qualification is attested. Separate
fictional Daycare and K–12 age groups remain distinct.

The existing `buyer-care-<school UUID>` internal plan code is reused because the
real Daycare service independently enforces its exact-school expiring module.
The presenter never acquires a buyer invitation or buyer-workspace binding.
Expired terms are not renewed by reseeding. Existing tenant/billing/custody rows
cause refusal and all fixture writes commit together.

Normal accounts and product API routes apply. Daycare Director/Staff use the
Daycare custody operations. The school administrator uses existing authorized
AM/PM and Camp operations; no global permission is added to a daycare role.
Parent readback requires the real household/account relationship.

Camp registration remains BLOCKED pending missing forms, health review and
pickup clearance. The public Camp API currently lacks a complete ordinary
forms/health clearance mutation path. Configuration, registration and blocked
admission can be demonstrated; complete ready-to-attend Camp clearance and
custody cannot yet be claimed. Never set clearance flags to manufacture proof.

Bootstrap destructive reset refuses populated care/entitlement/retained-history
models. Academic archive remains available for classroom practice. Whole-school
care/financial replay needs a separately verified retention-aware lifecycle;
this increment does not delete custody history or silently re-enroll a child.

Acceptance uses normal password login, real API mutations, independent readback,
persisted records, role denial, foreign tenant denial and expired-license denial.
API readback is not browser reload evidence. Existing PostgreSQL concurrency and
Windows/browser suites remain additional required evidence.

Azure activation remains NO-GO: these commands require the exact isolated local
SQLite database and reject hosted identities/PostgreSQL. A future owner must
approve a reviewed hosted presenter lane and an exact source revision separately;
never override the guards, import SQLite or use a prospect invitation as a
substitute universal environment.
