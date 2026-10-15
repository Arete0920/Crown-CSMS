# Jireh Financial Aid — Azure staging candidate (NOT DEPLOYED)

First product website migration: **the entire Jireh financial-aid family**, not only Jireh SGO.

- Primary: CROWN Jireh mission-aligned school financial aid.
- Related pilot-development offering: Jireh SGO scholarship-grantor administration.
- Site source: `sites/jireh/index.html`
- Shared family-wide appearance: `sites/shared/product-theme.css`
- Built output: `sites/jireh/dist/` (generated; do not commit)
- **No Azure deployment, paid service or GoDaddy DNS change is authorized by this PR.**

## Build and test

```bash
node --test sites/jireh/tests/site.test.mjs
node sites/jireh/build.mjs
python3 -m http.server 8090 --directory sites/jireh/dist
```

Azure Static Web Apps build configuration when Azure inventory/budget approval and a deploy plan exist:

- app_location: `sites/jireh`
- app_build_command: `node build.mjs`
- output_location: `dist`
- api_location: unset (no demo registration API has been accepted)
- default domain until DNS/CNAME prevalidation and cost approval

## Migration source and uncompleted dependency list

Original site sources:
- https://areteadvisorygroup.com/jireh
- https://areteadvisorygroup.com/jireh-sgo
- https://areteadvisorygroup.com/resources/jireh-sgo-overview.pdf
- https://areteadvisorygroup.com/images/jireh-sgo/logo.png

The original imagery and downloadable PDF have NOT been fully exported or parity-verified. This site uses self-contained conceptual CSS/HTML hero artwork intentionally instead of a misleading screenshot. In the staged build, overview PDF, legal links and contact requests still point to the existing Arete website. Independently test the link targets and migrate/secure the original assets prior to main-site retirement.

The first-party lead/demo registration service is NOT implemented or certified; existing contact CTA is a transitional handoff, not a guaranteed booking. Confirm end-to-end persistence, acknowledgment, sales routing, calendar booking, consent, abuse prevention and fault recovery before claiming instant scheduling.

Required gates: read-only authenticated Azure subscription/RBAC/spend/alerts/quotas/resource inventory, GoDaddy authoritative DNS and email record export, security and audit review, source-asset ownership, functional QA, accessible desktop/mobile/browser verification, staging TLS, cost approval, and tested reversible single-hostname cutover. Do not conflate production-ready marketing with production-ready financial-aid processing.

## Exported source assets

The SGO PDF, the official SGO logo, and the CROWN family billing concept image are vendored in the site source and copied into the staging output by `build.mjs`. Confirm owner rights and visual parity in browser QA; `https://areteadvisorygroup.com/contact`, privacy and terms remain live links for the transition.
