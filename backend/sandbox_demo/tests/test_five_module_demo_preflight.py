"""Local demo route evidence must adapt as unmerged modules become available."""
from pathlib import Path

from django.test import SimpleTestCase

from sandbox_demo.management.commands.five_module_demo_preflight import frontend_route_evidence


class FiveModuleRouteEvidenceTests(SimpleTestCase):
    def test_no_application_is_marked_available_without_verified_route_and_page(self):
        result = frontend_route_evidence("", "")
        self.assertEqual(len(result), 5)
        self.assertFalse(any(result.values()))

    def test_all_five_routed_modules_are_recognized_without_code_changes(self):
        paths = """
            FINANCIAL_AID PARENT_FINANCIAL_AID JIREH_SGO
            BEFORECARE_DIRECTOR AFTERCARE_DIRECTOR
            DIADEM_DIRECTOR SUMMER_CAMP_ROSTER
        """
        router = """
            PATHS.FINANCIAL_AID FinancialAidDashboard
            PATHS.PARENT_FINANCIAL_AID ParentFinancialAidPreparationPage
            PATHS.JIREH_SGO JirehSGODashboard
            PATHS.BEFORECARE_DIRECTOR CareSessionDirectorDashboard
            PATHS.AFTERCARE_DIRECTOR CareSessionDirectorDashboard
            PATHS.DIADEM_DIRECTOR DiademDirectorRosterPage
            PATHS.SUMMER_CAMP_ROSTER SummerCampRosterPage
        """
        self.assertTrue(all(frontend_route_evidence(paths, router).values()))

    def test_current_repository_route_evidence_is_dynamic(self):
        # This test must still pass after Jireh SGO and Diadem routes are added.
        root = Path(__file__).resolve().parents[3]
        routes = root / "frontend" / "dashboards" / "src" / "routes"
        result = frontend_route_evidence(
            (routes / "paths.js").read_text(encoding="utf-8"),
            (routes / "router.jsx").read_text(encoding="utf-8"),
        )
        self.assertEqual(set(result), {
            "Jireh Financial Aid", "Jireh SGO", "Extended Care",
            "Diadem Daycare", "Summer Camp",
        })
        self.assertTrue(result["Jireh Financial Aid"])
        self.assertTrue(result["Extended Care"])
        self.assertTrue(result["Summer Camp"])
        self.assertTrue(all(isinstance(ready, bool) for ready in result.values()))
