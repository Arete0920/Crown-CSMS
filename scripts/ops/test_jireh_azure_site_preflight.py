import unittest
from jireh_azure_site_preflight import collect


class JirehAzurePreflightTests(unittest.TestCase):
    def test_free_tier_does_not_imply_cost_or_launch_approval(self):
        calls = []
        def run(args):
            calls.append(args)
            if args[1:3] == ['account', 'show']:
                return {'id': 'fake', 'state': 'Enabled'}
            if args[1:3] == ['staticwebapp', 'list']:
                return [{'name': 'crown-dash', 'sku': {'name': 'Free'}},
                        {'name': 'jireh-site', 'sku': {'name': 'Free'}}]
            if args[1:3] == ['consumption', 'budget']:
                return [{'name': 'budget'}]
        data = collect(run=run)
        self.assertEqual(data['static_sites']['sku_counts'], {'Free': 2})
        self.assertTrue(data['static_sites']['existing_jireh_site'])
        self.assertEqual(data['budget_count'], 1)
        self.assertFalse(data['launch_authorized'])
        self.assertEqual(data['actual_cost_status'], 'NOT_COLLECTED')
        self.assertEqual(len(calls), 3)
        self.assertTrue(all('create' not in arg and 'update' not in arg and 'delete' not in arg
                            for args in calls for arg in args))
    def test_no_cli_access_fails_closed_without_implicit_zero(self):
        data = collect(run=lambda _: None)
        self.assertEqual(data['checks']['static_web_apps'], 'UNAVAILABLE')
        self.assertEqual(data['checks']['resource_group_budgets'], 'UNAVAILABLE')
        self.assertIsNone(data['budget_count'])
        self.assertFalse(data['launch_authorized'])
    def test_rejects_bad_resource_groups(self):
        for group in ('', '../bad', 'x; rm -rf /', 'invalid group'):
            with self.assertRaises(ValueError):
                collect(group, run=lambda _: None)


from jireh_azure_site_preflight import AdmissionDenied, plan, verify

def site(name="jireh-site", group="crown-rg", sku="Free"):
    return {"name": name, "sku": {"name": sku},
            "id": f"/subscriptions/mock/resourceGroups/{group}/providers/Microsoft.Web/staticSites/{name}"}

class JirehAdmissionTests(unittest.TestCase):
    def test_reuse_existing_free_only(self):
        self.assertEqual(plan([site(), site(name="crown-dash")]), "REUSE_VERIFIED_FREE")
        self.assertTrue(verify(site()))
    def test_create_with_available_quota(self):
        self.assertEqual(plan([site("crown-dash")]), "CREATE_FREE")
    def test_fail_at_quota(self):
        with self.assertRaises(AdmissionDenied):
            plan([site(name=f"free-{x}") for x in range(10)])
    def test_never_replace_paid(self):
        with self.assertRaises(AdmissionDenied):
            plan([site(sku="Standard")])
        with self.assertRaises(AdmissionDenied):
            verify(site(sku="Standard"))
    def test_other_resource_group_fails(self):
        with self.assertRaises(AdmissionDenied):
            plan([site(group="other-rg")])
        with self.assertRaises(AdmissionDenied):
            verify(site(group="other-rg"))
    def test_unavailable_inventory_fails(self):
        for bad in (None, {}, [dict(name="jireh-site")], [site(sku="Unknown")]):
            with self.subTest(value=bad), self.assertRaises(AdmissionDenied):
                plan(bad)
    def test_duplicate_name_fails(self):
        with self.assertRaises(AdmissionDenied):
            plan([site(), site()])
    def test_rejects_command_injection_names(self):
        for value in ("", "../bad", "a b", "x;curl"):
            with self.subTest(value=value), self.assertRaises(AdmissionDenied):
                plan([], name=value)

if __name__ == "__main__":
    unittest.main()
