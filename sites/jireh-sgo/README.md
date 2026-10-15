# Jireh SGO — Azure staging candidate (NOT DEPLOYED)

This folder contains a scoped, self-contained static marketing page based on Arete's existing **/jireh-sgo** page and October 2026 two-page overview. Product status remains **pilot development**. This work does not activate a product portal or scholarship funds movement.

## Test

```bash
node --test tests/site.test.mjs
```

Serve this folder locally with any static HTTP server, for example:

```bash
python3 -m http.server 8090 --directory sites/jireh-sgo
```

## Azure Static Web Apps settings (after authorized read-only Azure inventory)

- App location: `sites/jireh-sgo`
- Output location: empty (static files, no build step)
- API location: empty (no API; future demo lead handling must be separately certified)
- Branch: approved default branch after governed merge
- Free tier for preproduction validation; production plan cost requires owner authorization

**Deployment intentionally not configured:** No Azure account access, resource ID or secret has been verified. Do not add an auto-deploy workflow or paid resource until the Azure preflight is accepted.

## Legacy dependencies and cutover blockers

1. The original downloadable PDF is still hosted at `https://areteadvisorygroup.com/resources/jireh-sgo-overview.pdf`. The original PDF bytes must be lawfully exported and stored locally at `resources/jireh-sgo-overview.pdf` before a GoDaddy/legacy source cutover.
2. The original Jireh SGO logo at `https://areteadvisorygroup.com/images/jireh-sgo/logo.png` is not yet exported or visually verified. This staging page deliberately uses a typographic brand instead of falsely claiming asset parity; obtain the official image and review branding before launch.
3. Registration CTA currently points to the existing Arete contact path with product topic. Its persistence, notifications, and calendar confirmation have not been independently tested; do not call it certified demo booking.
4. Privacy and Terms currently link to the existing Arete pages. Their versioned copies or independently validated continuing availability are required before any original-domain retirement.
5. `robots.txt` and meta robots explicitly block indexing during staging. Remove only as part of a verified, approved production release.
6. Current website content was researched from the live public site, not from an authenticated GoDaddy site export; confirm originals, ownership and all URLs.

## Release criteria

- Azure account/subscription, resource inventory, RBAC, costs/budget, tenant, security and DNS independently evidenced;
- original content/logo/PDF and legal notices reconciled; no hidden dependency on the retiring host;
- accessible desktop/mobile and browser tests pass; legal/program claims approved;
- real demo registration storage, notifications, anti-abuse measures and consent tested before public booking claims;
- staging custom hostname/HTTPS, synthetic end-to-end tests, backup/rollback evidence complete;
- explicit approval for any recurring charges, domain or DNS changes.

No live DNS changes or production certification are asserted by this code.
