# Sandbox SWA redeploy marker

Created: 2026-06-23

Purpose: force a main-branch push after the Azure Static Web Apps SPA routing fix and dashboard deploy workflow repair were merged.

Expected live validation after deployment:

- https://crown-sandbox.azurestaticapps.net/login serves CROWN instead of Azure 404.
- https://crown-sandbox.azurestaticapps.net/sandbox serves CROWN instead of Azure 404.
- https://crown-sandbox.azurestaticapps.net/build.json reports the current main deployment SHA.
