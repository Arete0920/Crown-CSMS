"""Read-only tests of DEV preview workflow authority and mutation gates."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
class DevPreviewAuthorityTests(unittest.TestCase):
    def setUp(self):
        y = yaml.safe_load((ROOT / ".github/workflows/deploy-dashboard.yml").read_text())
        self.job = y["jobs"]["dev-certification-preview"]
        self.steps = {s.get("name"): s for s in self.job["steps"] if s.get("name")}
        self.names = [s.get("name", "") for s in self.job["steps"]]

    def test_protected_main_dispatch_and_workflow_identity(self):
        self.assertIn("github.ref == 'refs/heads/main'", self.job["if"])
        self.assertEqual(self.job["environment"], "dev")
        s = self.steps["Require exact current protected main"]
        self.assertEqual(s["env"]["WORKFLOW_SHA"], "${{ github.sha }}")
        for marker in ('"$GITHUB_REF" != "refs/heads/main"',
                       '"$GITHUB_EVENT_NAME" != "workflow_dispatch"',
                       '"$SOURCE_SHA" != "$WORKFLOW_SHA"',
                       '"$(git rev-parse HEAD)" != "$SOURCE_SHA"',
                       '"$SOURCE_SHA" != "$CURRENT_MAIN_SHA"'):
            self.assertIn(marker, s["run"])
        self.assertLess(self.names.index("Require exact current protected main"),
                        self.names.index("Authenticate existing Azure DEV deployment identity"))

    def test_write_stages_recheck_protected_main(self):
        self.assertEqual(self.names[self.names.index("Deploy preview on existing SWA only")-1],
                         "Recheck exact main before preview upload")
        self.assertEqual(self.names[self.names.index("Configure exact owned DEV preview origin")-1],
                         "Recheck current main before DEV CORS appsettings")
        for name in ("Recheck current main before DEV CORS appsettings",
                     "Recheck current main before DEV browser certification"):
            step = self.steps[name]
            self.assertIn("git fetch --no-tags origin refs/heads/main:",step["run"])
            self.assertIn('"$SOURCE_SHA" != "$WORKFLOW_SHA"',step["run"])
        for name in ("Configure exact owned DEV preview origin",
                     "Execute existing live certification against DEV preview",
                     "Execute existing buyer persistence journeys on DEV",
                     "Prepare two synthetic DEV tenants using existing models",
                     "Execute existing Playwright framework for two-tenant HTTP isolation"):
            s = self.steps[name]
            self.assertEqual(s["env"]["SOURCE_SHA"], "${{ inputs.dev_source_sha }}")
            self.assertIn("git fetch --no-tags origin refs/heads/main:",s["run"])
            self.assertIn('"$(git rev-parse refs/remotes/origin/main)" != "$SOURCE_SHA"',s["run"])
        cors = self.steps["Configure exact owned DEV preview origin"]["run"]
        self.assertLess(cors.index("git fetch --no-tags origin refs/heads/main:"),
                        cors.index("az webapp config appsettings set"))
        tenant = self.steps["Prepare two synthetic DEV tenants using existing models"]["run"]
        self.assertLess(tenant.rindex("git fetch --no-tags origin refs/heads/main:"),
                        tenant.index("python - <<'PYCODE'"))
if __name__ == "__main__":
    unittest.main()
