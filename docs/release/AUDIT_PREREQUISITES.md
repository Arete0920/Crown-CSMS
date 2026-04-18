# AUDIT PREREQUISITES

## Required for a complete audit pack
- Working Python executable
- Installed backend requirements
- `django-extensions` installed and enabled in `INSTALLED_APPS`
- Authenticated GitHub CLI (`gh auth status`)
- Reachable health base URL, or local server on `127.0.0.1:8000`

## Branch protection note
Branch protection retrieval uses GitHub API access and may return `403` if the authenticated identity lacks permission. That cannot be fixed by repo code alone.