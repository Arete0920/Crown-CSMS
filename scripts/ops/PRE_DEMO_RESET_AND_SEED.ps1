# Retired unsafe wrapper: the historical script ran manage.py flush --noinput,
# which deletes every row in whichever database Django happens to select.
# Host-name checks and an interactive -Force bypass did not establish that the
# database contained only disposable Heritage test data.
#
# This script deliberately performs no database or filesystem operations.
# To reset an isolated Heritage fixture, use tools/demo_reset_smoke.ps1 with
# an explicit school UUID and the independent operator-set safety approvals.
$ErrorActionPreference = "Stop"
throw "PRE_DEMO_RESET_AND_SEED is retired: unscoped database flush is forbidden. Use tools/demo_reset_smoke.ps1 with an explicit HeritageSchoolId, isolated local SQLite DATABASE_URL, CROWN_ENV=local, CROWN_ALLOW_DEMO_WIPE=true and -ConfirmDemoWipe."
