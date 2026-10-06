# CROWN2026 â€” PRIORITIES 32â€“46 TO GREEN

> **Superseded authority notice (2026-10-05):** This predecessor priority list is retained for provenance only. It is not a current work queue or release authority source.


32. Release patch idempotency
Green when duplicate injected blocks in settings.py and urls.py are normalized and reported.
33. Release package readiness
Green when required backend/frontend release-closeout packages are present and a package report is clean.
34. Canonical report and closeout route catalog
Green when report/release-closeout routes are enumerated and written to a manifest.
35. Release route contract tests
Green when release-closeout and report routes resolve and return expected status/content type.
36. PDF header contract
Green when report endpoints emit application/pdf and attachment headers.
37. Frontend release API unification
Green when auth token, school header, and timeout handling are centralized.
38. Stable release export controls
Green when export controls expose data-testid markers and use the shared API client.
39. Deterministic auth golden path
Green when Playwright login uses env-driven credentials and stable selectors.
40. Accessibility smoke
Green when axe scans pass on login/admin/parent/teacher/student routes.
41. CompuWerx sandbox evidence
Green when sandbox verification writes a dated proof file or a hard fail artifact.
42. Seed/fixture parity
Green when release demo seed manifest exists and parity scan is clean.
43. Workflow preflight
Green when workflow names, lockfile references, and required checks validate.
44. Release environment matrix
Green when dev/staging/prod expectations are documented in one canonical file.
45. Release status matrix widget
Green when a small frontend widget reads release-closeout status and exposes test ids.
46. Release doctor
Green when one command runs patch guard, package readiness, route tests, frontend smoke, sandbox proof, manifests, and writes a doctor summary.