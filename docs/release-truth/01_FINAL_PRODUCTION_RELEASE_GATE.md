# Crown Final Production Release Gate

## Gate Status
- [ ] Core proof green
- [ ] Auth / RBAC / tenant isolation green
- [ ] Core route-contract integrity green
- [ ] Admissions green end to end
- [ ] Re-enrollment green end to end
- [ ] Billing / payments green end to end
- [ ] Communications and role-based portals green for agreed scope
- [ ] No manual patching on critical flows
- [ ] No demo-only exceptions
- [ ] No deferred items inside claimed release scope
- [ ] Full regression green
- [ ] Deploy / release verification green
- [ ] Evidence pack current and stored in canonical location
- [ ] README / CHANGELOG / SECURITY / COMPLIANCE / MODULE_INVENTORY aligned
- [ ] TC sign-off complete

## Required Proof Per Area
| Area | Must Be True | Evidence Path | Owner | Date Verified | Status |
|---|---|---|---|---|---|
| Core | Core contracts stable | | Dev 1 | | |
| Tenant/RBAC | Negative tests green | | Dev 1 / Dev 5 | | |
| Admissions | Inquiry to enrolled works | | Dev 3 | | |
| Re-enrollment | Returning student flow works | | Dev 3 | | |
| Billing | Charges, balances, payment record path works | | Dev 3 | | |
| Communications/Portals | Parent/teacher/admin views reflect truth | | Dev 4 | | |
| Regression | Full suite green for release scope | | Dev 5 | | |
| Deploy | Main release path green | | Dev 5 | | |
| Docs | Public/internal docs match reality | | Docs | | |

## Executive Rule
If any row above is not green, final production-ready release cannot be claimed.
