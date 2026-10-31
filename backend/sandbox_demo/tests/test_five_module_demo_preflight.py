"""No database mutation required for the local five-module preflight contract."""
from django.test import SimpleTestCase
from sandbox_demo.management.commands.five_module_demo_preflight import frontend_route_evidence


class FiveModuleRouteEvidenceTests(SimpleTestCase):
    def test_missing_module_cannot_be_reported_as_routed(self):
        result = frontend_route_evidence("FINANCIAL_AID: '/financial-aid'", "PATHS.FINANCIAL_AID FinancialAidDashboard")
        self.assertTrue(result["Jireh Financial Aid"] is False)
        self.assertFalse(result["Diadem Daycare"])
        self.assertFalse(result["Jireh SGO"])

    def test_complete_source_route_indicators(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[4]
        routes = root / "frontend" / "dashboards" / "src" / "routes"
        result = frontend_route_evidence(
            (routes / "paths.js").read_text(encoding="utf-8"),
            (routes / "router.jsx").read_text(encoding="utf-8"),
        )
        self.assertTrue(result["Jireh Financial Aid"])
        self.assertTrue(result["Extended Care"])
        self.assertTrue(result["Summer Camp"])
        self.assertFalse(result["Jireh SGO"])
        self.assertFalse(result["Diadem Daycare"])
