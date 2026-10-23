# CROWN Logo Placement Matrix — Controlled

Source: `frontend/dashboards/src/brand/crownBrandAssets.js` at audited main commit `c22cb5db4cb085f3e8fa44ffc673f88a8c204f5d` (2026-10-23). Verify against the current source before release; do not infer deployed revision from this table.

| UI surface / key | Runtime canonical variant |
| --- | --- |
| sidebarExpanded | horizontal |
| sidebarCollapsed | crown mark |
| topnavHorizontal | horizontal |
| loginBrand | primary stacked |
| dashboardHero | horizontal |
| printHeader | horizontal |
| emailHeader | horizontal |
| reportCover | primary stacked |
| Direct `CrownLogo variant="horizontal"` | horizontal |
| Direct `CrownLogo variant="mark"` | crown mark |

All items above resolve to `/brand/crown/logo/` assets via shared frontend branding components. Historical role-named SVGs under `/brand/crown/ui/` remain compatibility/provenance artifacts, **not** the active resolution paths. Preserve them until a separate reference and release verification permits their removal.

Formal use may select the registered shield, wordmark, square mark, compact or monochrome variants as appropriate. The CROWN brand guide governs palette and rights review. Microsoft-branded placements may only use official, licensed/provenanced assets; otherwise use the existing safe text fallback.
