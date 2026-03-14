from django.test import SimpleTestCase, override_settings

from payments.webhooks import verify_compuwerx_signature


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
class CompuwerxSignatureVerificationTests(SimpleTestCase):
    def test_invalid_signature_fails(self):
        self.assertFalse(verify_compuwerx_signature(b'{"ok":true}', "bad-signature"))
