# Apple Wallet Pass Template

This directory contains the `pass.json` template and required image assets
for Apple Wallet `.pkpass` generation.

## Required image files (place here before deploying)

Apple PassKit requires these image files (PNG, exact names):

| File           | Size (1x)   | Size (2x)    | Size (3x)    |
|----------------|-------------|--------------|--------------|
| `icon.png`     | 29 × 29 px  | `icon@2x.png` 58×58 | `icon@3x.png` 87×87 |
| `logo.png`     | 160 × 50 px | `logo@2x.png` 320×100 | — |
| `strip.png`    | 375 × 123 px | `strip@2x.png` 750×246 | — |

> **Note:** At minimum `icon.png` and `icon@2x.png` are required by PassKit.
> Without them `passkit-generator` will throw an error.

## Customisation

- Edit `pass.json` to update `backgroundColor`, `foregroundColor`, `logoText`.
- Replace `strip.png` / `logo.png` with school branding.
- The `passTypeIdentifier` and `teamIdentifier` in `pass.json` are overridden
  at runtime by the service — you can leave them as placeholders.

## Cert material (never commit)

Mount via Docker volume at the paths set in env vars:
- `APPLE_PASS_CERT_P12_PATH` → your signing certificate (p12)
- `APPLE_WWDR_PEM_PATH`      → Apple WWDR G4 PEM (download from developer.apple.com)

Store these in `secrets/apple/` (gitignored) and mount read-only in docker-compose.
