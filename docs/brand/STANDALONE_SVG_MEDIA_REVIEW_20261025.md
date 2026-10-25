# CROWN standalone SVG embedded-media change evidence — 2026-10-25

Change owner: repository protected-merge review; source baseline: `565b98191dc584f2d5d0ed64235590847a600462`. Tracking: issue #450 / PR #452.

## Change and decoded-content review
These three existing, canonical variants previously referenced sibling SVG files using relative `<image href>`. The changed variants embed unchanged source artwork using percent-encoded `data:image/svg+xml;charset=utf-8,` payloads. The canonical source artwork remains unmodified. Exact decoded-byte comparisons for all three variants matched their original canonical files. Neither scripts nor external network image references are introduced.

| Reviewed variant | SHA-256 of changed SVG |
| --- | --- |
| `crown-logo-mark-square.svg` | `c3c87898050a98b3dc217afdc11a4fb31a98dc9668cafc938d4d4b679a5d1939` |
| `crown-logo-monochrome-royal.svg` | `fa8b9dcd35deb5c0eb7f78bb2d471c3753bb7e3398678b07fa825f8e6db79007` |
| `crown-logo-monochrome-white.svg` | `258905c6067f52aa70293e5d9cf7a35fe392e06d47e480bf896e34df732775ab` |

Source payload checksums were calculated against exact GitHub file contents and the hash implementation passed standard SHA-256 test vectors. The unmodified crown-only and horizontal full-color SVGs match their existing registry checksums. Changing artwork alters checked media bytes, so the three revised checksums are explicitly admitted in the existing strict registry; all unrelated hashes remain unchanged.

## Visual QA and remaining hold
The PR adds a Chromium Playwright browser test that loads the variants as HTML image elements, asserts an SVG response and nonzero image dimensions, checks for visible canvas pixels, and uploads screenshots under a seven-day retention. **This document is a pre-execution review record, not a claim that rendered QA passed.** The existing policy gate, browser checks, focused Vitest and required workflows must be terminal-green on the exact PR head before merger. Human design/rights acceptance and live Azure verification remain separate buyer-IP release gates. No asset deletion, vendor logo substitution, payments or production activation is authorized.
