# Brand Asset Intake and Buyer IP Evidence Checklist

Status: INTERNAL WORKING CONTROL, audit dated **2026-10-23**. No assurance that the whole Drive, past Git history, Azure deployed content, laptops, websites, legal files, or outside storage has been inspected. Do not circulate unapproved files as buyer-ready.

## Required production asset intake

1. **CROWN favicon set:** `frontend/dashboards/public/brand/crown/favicon/favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`. None of those paths appeared in the audited default-branch tree; this is **missing-file evidence**, not proof that no favicon is deployed elsewhere.
2. **Microsoft third-party assets:** the existing `frontend/dashboards/public/brand/third-party/microsoft/manifest.json` lists 17 entries with null paths. Acquire original official Microsoft artwork only where licensed/authorized and record asset, origin, retrieval date, permitted use and reviewer in the source register. Do not generate replacements. Text fallback remains safer than unverifiable marks.
3. **CROWN nine canonical SVG variants:** present in default-branch tree. Test actual render, cross-device backgrounds, image export/print, packaging, accessibility/alt text, source-file portability and rights provenance. Some full-color SVGs embed PNG data; some monochrome assets reference other files.

## Verified 2026-10-23 non-destructive repository evidence

- GitHub `Arete0920/Crown-CSMS`, main SHA `c22cb5db4cb085f3e8fa44ffc673f88a8c204f5d`; recursive tree was not truncated, 6,010 entries.
- Extension-only image/PDF inventory: **20 SVG, 6 WEBP, 1 PNG, 1 PDF** (28 files); embedded images in documents, nonstandard extensions, branches, website uploads and deployed assets are outside that count.
- One Git blob SHA `8e53309fb9c558790a6552303bcdd95293d6cb34` occurs in **eight** public-brand SVG paths (legacy lockup plus seven UI aliases). SHA `3ec06e520ce22350617d51d59ebecc55d0db34f6` occurs in **two** paths (legacy mark and sidebar collapsed alias). This gives eight content-redundant instances across the groups; all preserved pending dependency/deploy review.
- The active stylesheet and July 2026 CROWN Style Guide agree on `--crown-primary: #2a5ec4`, `--crown-gold: #c28a24`; legacy repository logo instructions and the separate CROWN manifest color block disagreed. Use the live CSS palette for application tokens, but do not arbitrarily recolor approved image masters.

## Verified Google Drive findings (Drive originals NOT changed)

- **Images — Unsorted Uploads** folder: https://drive.google.com/drive/folders/1Qx_nkAmSDCZ2zHhCAkPHKKaE3qPKisup. Two paginated listing results total **168 PNGs**, organized by **84 repeated-name-and-size pairs**. Exactly **three pairs** were compared as raw bytes and confirmed equal. The other **81 pairs** remain unverified candidates.
- Raw-byte-verified duplicates in separate folders: three `Crown2026_Code_Escrow_and_IP_Record.docx` items (IDs `1ujVSmJHETgtTgdxCSPcI5qSnAuCyqwaJ`, `1-3pba61mqejky6PYZE199Cfdobu2J-ab`, `10P4SLuMR4fr_ALYCWgJIU6OKYG8teOHr`); three identical `CROWN_2026_Investor_40min_Deck_LOCKED_Images.pptx` items (IDs `1EbKqE4v_dyUDxZ3EsU63YJ4a7spGOe8O`, `1s13Pus3g3cH1x2B0cu2j9z3vMxD_9XIE`, `1yVF-4Utlme8BIU-LNWEpmOLm0yQEUAlV`); two identical `CROWN_Comprehensive_Investor_Proposal_V3.docx` items (IDs `1QulyUOb7qP6SxWUic-LQT1581wlCMukP`, `1XBs41o-62VV_NTqT0boG9vmpAz1lW-97`). A same-named 963,215-byte deck (ID `1q2Fumfsye8_jrwkmNVZrzil1j-MesxpY`) was **not** identical to the 963,197-byte decks: do not collapse it.
- Two inspected PNG marketing posters (example IDs `1kaV8FW_S6kOXVpe7wRVICgQqF1Krh2mO`, `1ErqD3he9CcjkcItBh_mX8xD3bafyldYs`) announce **Launching October 2026**; they are outdated for current distribution. One also needs evidence for security/integration claims. Hold for review rather than silently editing originals.
- The controlled Drive document index remains https://docs.google.com/document/d/132Qa6_y7kXZrw03WozxCvKEONdLiVqNgaci8AXYyMls/edit. An attempted 2026-10-23 append was denied **HTTP 403 permission**, so there was no verified Drive write and no Drive archival move/delete.

## Buyer-facing evidence gates

1. **Current versions:** identify one reviewed authoritative source for public product terms, slides, screenshot/artwork, manuals, deployment claims and dated technical evidence. Older October 5 buyer/marketing files include superseded school setup and household-cap figures. Never use a `FINAL` or `LOCKED` filename as proof of current approval.
2. **IP chain of title:** confirm legal owner for CROWN code, artwork, logos, marks, Arete/Diadem/Jireh/Kairos/Solomon/Scribe assets, source design files, contractor contributions, domains and any rights transfers. The 2026-01-15 Crown2026 IP/escrow record is historical, not proof of executed escrow or current assignment. Repository `NOTICE.md` asserts proprietary rights, not documented title or trademark registration.
3. **License inventory:** prove image/font/icon provenance, third-party artwork permissions, source attributions, code/dependency licenses and restrictions, and clarify rights retained or excluded by Arete Advisory Group in any sale.
4. **Claims and confidentiality:** withhold dated launch posters, unverifiable customer/production counts, unverified security and Azure/payment claims, and obsolete financial models. Disclose public source visibility and counsel-reviewed trade-secret implications accurately.
5. **Duplicate archival policy:** create byte/hash evidence per file, decide a canonical ID, map backlinks and permissions, preserve original and lineage, label copies `HISTORICAL`/`SUPERSEDED` after authorization, and delete only after retention/counsel signoff. No automatic or destructive cleanup.
6. **Controlled buyer export:** produce a dated checksum manifest of approved files, content lineage and permissions; exclude secrets, personal information and development-only artifacts; require approval before external share.

## Execution checks before closure

- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/brand/check_brand_asset_readiness.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/brand/verify_brand_integrity.ps1`
- `cd frontend/dashboards && npm run build`
- `cd frontend/dashboards && npm run test -- src/components/brand/CrownLogo.test.jsx src/components/brand/MicrosoftProductLogo.test.jsx src/tests/brandIntegrity.test.js src/tests/loginPagePolish.test.jsx src/tests/dashboardCardContract.test.jsx`
- `cd frontend/dashboards && npm run test:contracts && npm run ci:shell`

Release acceptance requires verified checks, design review, permissions and IP evidence. **No checks or builds were executed by the 2026-10-23 connector-only audit.** Historical or duplicate content was not removed; remaining brand buyer-readiness holds are OPEN.
