# CROWN Logo Style Guide — Controlled Repository Reference

Status: CURRENT REPOSITORY USE GUIDE (2026-10-23). This guide governs source-code asset selection; it does not certify artwork ownership, trademark registration, complete asset provenance, live deployment, or legal transferability.

## Identity

- Product name: **CROWN**
- Approved descriptor: **Christian School Management Solution**
- Public lockup: **CROWN Christian School Management Solution**
- Use **CROWN**, not **Crown2026**, in current user-facing content.
- Do not substitute emoji crowns, unapproved variants, or third-party marks.

## Source of truth and color tokens

- Runtime logo paths: `frontend/dashboards/src/brand/crownBrandAssets.js`.
- Original registered paths: `frontend/dashboards/public/brand/crown/logo/`.
- Runtime design palette: `frontend/dashboards/src/styles/crown-theme.css`.
- Companion visual authority: **CROWN Style Guide, Version 2.0 (July 2026)** in the controlled Drive materials.
- Current theme is **light-royal, light surfaces only**. Key tokens: `--crown-bg: #f8fbff`, `--crown-primary: #2a5ec4`, `--crown-primary-deep: #173f91`, `--crown-gold: #c28a24`. Use CSS variables rather than adding hardcoded colors.
- If color values in `frontend/dashboards/public/brand/crown/manifest.json`, older brochures, or historical art conflict with the active token file, treat the conflict as an audit issue. Do not silently recolor approved logos.

## Nine canonical logo files

| Variant | File | Intended use |
| --- | --- | --- |
| Primary stacked | `crown-logo-primary-stacked-full-color.svg` | Login, onboarding, cover |
| Horizontal | `crown-logo-horizontal-full-color.svg` | Navigation, landing, reports |
| Compact | `crown-logo-compact-full-color.svg` | Compact headers |
| Wordmark | `crown-logo-wordmark-full-color.svg` | Text-led documents |
| Crown mark | `crown-logo-mark-crown-only.svg` | Sidebar collapsed, small accents |
| Shield mark | `crown-logo-mark-shield.svg` | Formal and governance use |
| Square mark | `crown-logo-mark-square.svg` | App icons, subject to favicon export QA |
| Royal monochrome | `crown-logo-monochrome-royal.svg` | Permitted single-color application |
| White monochrome | `crown-logo-monochrome-white.svg` | Only against approved deep-royal field |

Preserve proportional scaling, approved clear space, cross/crown geometry and legibility. Route frontend rendering through shared components in `frontend/dashboards/src/components/brand/`; do not add page-specific hardcoded logo URLs. `CROWN_LOGO_PLACEMENT_MATRIX.md` maps intended placements.

## Preservation and reproduction warnings

- The active nine canonical file names are separate from *legacy compatibility alias files* under `public/brand/` and `public/brand/crown/ui/`. Do not delete these aliases without dependency, rendered-output, rollback and deployment verification.
- The full-color SVG lockups inspected on 2026-10-23 embed PNG imagery; they are SVG containers, not fully editable vector artwork. The inspected royal monochrome SVG uses a relative reference to the horizontal SVG. Test portability in email, presentation, print/export and offline conversion before representing the supplied set as standalone editable masters.
- Do not alter the logo merely to resolve visual differences between historical creative material and the active application.
- Metadata or matching filenames do not establish copyright, trademark rights, source-image licenses or executed IP assignment. Buyer use requires separately documented rights/provenance.

## Evidence and release gates

The non-destructive 2026-10-23 review of main SHA `c22cb5db4cb085f3e8fa44ffc673f88a8c204f5d` found nine canonical logo variants and two groups of identical-content UI/legacy SVG aliases; no asset removal was authorized. See the intake checklist for missing favicons, third-party asset provenance and buyer-facing artwork/documentation hold conditions. Require passing asset readiness, visual QA and approved protected-branch workflow before stating brand implementation is certified.
