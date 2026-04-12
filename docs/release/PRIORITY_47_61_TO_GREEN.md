# CROWN2026 - PRIORITIES 47-61 TO GREEN

47. W002 offender inventory
Green when the repo writes a ranked per-file W002 inventory and summary.
48. W002 budget gate
Green when the current count is checked against a ratcheting budget file.
49. Function-view schema auto-patch
Green when bare @api_view endpoints get a generic response schema.
50. APIView method schema auto-patch
Green when bare get/post/put/patch/delete/list/retrieve/create/update/destroy methods get a generic response schema.
51. Ledger and auth closeout
Green when ledger/api.py and core/auth/views.py are included in the patch pass.
52. Remaining wizard tail sweep
Green when all *_wizard/views.py files are included in the patch pass.
53. Schema compile proof
Green when patched Python files are py_compile-clean.
54. Spectacular schema build proof
Green when spectacular exports docs/openapi/crown-openapi.yaml after the patch pass.
55. Route-to-schema manifest
Green when release and report routes are cataloged in audit-artifacts/release-manifest.
56. Schema progress document
Green when docs/release/SCHEMA_W002_PROGRESS.md reflects the latest verified count and top offenders.
57. Schema governance workflow
Green when CI runs inventory, schema export, and budget gate and uploads artifacts.
58. Schema governance pytest
Green when schema governance assets and summaries are tested.
59. Shared release API client
Green when frontend release widgets and export controls use one shared API client.
60. Schema status widget
Green when a frontend widget reads schema progress and exposes stable test ids.
61. Schema green pass command
Green when one repo-root command runs inventory, auto-patch, compile, deploy-check, schema export, gate, manifests, and writes a ship candidate.