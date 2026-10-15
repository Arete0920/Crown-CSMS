import unittest
from jireh_free_staging_gate import AdmissionDenied, plan, verify

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
