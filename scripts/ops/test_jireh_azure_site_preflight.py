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


if __name__ == '__main__':
    unittest.main()
