# Brand Asset Intake Checklist

Purpose:
- Close remaining Pass 1 blockers using official asset packages only.

## Required Intake Package

1. CROWN favicon set (required)
- frontend/dashboards/public/brand/crown/favicon/favicon.ico
- frontend/dashboards/public/brand/crown/favicon/favicon-16x16.png
- frontend/dashboards/public/brand/crown/favicon/favicon-32x32.png
- frontend/dashboards/public/brand/crown/favicon/apple-touch-icon.png
- frontend/dashboards/public/brand/crown/favicon/android-chrome-192x192.png
- frontend/dashboards/public/brand/crown/favicon/android-chrome-512x512.png

2. Microsoft official logos (required before final brand completion)
- Provide official files for all entries in frontend/dashboards/public/brand/third-party/microsoft/manifest.json
- Fill source details in:
  - frontend/dashboards/public/brand/third-party/microsoft/usage/microsoft-logo-source-register.md

## Evidence To Capture After Intake

1. Run readiness snapshot:
- powershell -NoProfile -ExecutionPolicy Bypass -File scripts/brand/check_brand_asset_readiness.ps1

2. Run integrity scan:
- powershell -NoProfile -ExecutionPolicy Bypass -File scripts/brand/verify_brand_integrity.ps1

3. Run frontend verification:
- cd frontend/dashboards
- npm run build
- npm run test -- src/components/brand/CrownLogo.test.jsx src/components/brand/MicrosoftProductLogo.test.jsx src/tests/brandIntegrity.test.js src/tests/loginPagePolish.test.jsx src/tests/dashboardCardContract.test.jsx
- npm run test:contracts
- npm run ci:shell

## Acceptance Signal

Pass 1 brand asset closure is complete when:
- CROWN manifest assets = 7/7 present
- CROWN favicons = 6/6 present
- Microsoft manifest assets = 17/17 present (official sourced)
- Integrity and frontend validations are green
