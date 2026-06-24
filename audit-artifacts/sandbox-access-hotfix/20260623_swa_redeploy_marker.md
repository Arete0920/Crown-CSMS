# Sandbox SWA redeploy marker

Created: 2026-06-23

Purpose: force a main-branch push after the Azure Static Web Apps SPA routing fix and dashboard deploy workflow repair were merged.

## Endpoint correction

Later 2026-06-23 Azure subscription verification proved that the CROWN Christian School Management subscription contains Static Web App `crown-dash` with default hostname:

- https://yellow-forest-0eecc8b0f.7.azurestaticapps.net

The previously tested/documented hostname below is not present as a Static Web App in the verified CROWN Azure subscription and must not be used for buyer or operator access:

- https://crown-sandbox.azurestaticapps.net

## Expected live validation after deployment

- https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/login serves CROWN instead of Azure 404.
- https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/sandbox serves CROWN instead of Azure 404.
- https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/build.json reports the current main deployment SHA.
