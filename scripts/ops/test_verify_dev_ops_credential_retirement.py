import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error
import urllib.parse


spec = importlib.util.spec_from_file_location(
    "credential_probe", Path(__file__).with_name("verify_dev_ops_credential_retirement.py"))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SHA = "a" * 40
OLD = "synthetic-retired-" + "x" * 40
NEW = "synthetic-replacement-" + "y" * 40


def health(**changes):
    return {
        **{"env": "dev", "ok": True, "db": "ok", "build_sha": SHA,
           "artifact_build_sha": SHA}, **changes}


class Response:
    def __init__(self, code, data=None, *, raw=None, forbid_read=False):
        self.code = code
        self.body = raw if raw is not None else json.dumps(data).encode()
        self.forbid_read = forbid_read
        self.read_sizes = []
        self.closed = False

    def read(self, size):
        if self.forbid_read:
            raise AssertionError("Unexpected response body was read")
        self.read_sizes.append(size)
        return self.body[:size]

    def close(self):
        self.closed = True


class Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class CredentialProbeTests(unittest.TestCase):
    def passing_opener(self, *, old_response=None, final_health=None):
        return Opener(Response(200, health()), Response(400, probe.MISSING_SCHOOL),
                      old_response or Response(403, {"detail": "Forbidden"}),
                      final_health or Response(200, health()))

    def test_pass_requires_exact_handlers_and_healthy_identity_without_closure_claim(self):
        opener = self.passing_opener()
        report = probe.probe(SHA, OLD, NEW, opener=opener)
        self.assertEqual(report["reset_credential_probe"], "PASS")
        self.assertEqual(report["diagnostic_authorization"], "NOT_TESTED")
        self.assertEqual(report["secret_store_and_consumer_retirement"], "NOT_VERIFIED")
        self.assertEqual(report["issue_269_closure"], "NOT_CERTIFIED")
        self.assertEqual(len(opener.requests), 4)
        for request in opener.requests:
            target = urllib.parse.urlsplit(request.full_url)
            self.assertEqual(target.scheme, "https")
            self.assertEqual(target.netloc, "crown-api-dev.azurewebsites.net")
            self.assertEqual(target.query, "")
            self.assertEqual(target.fragment, "")
            headers = {k.lower(): v for k, v in request.header_items()}
            self.assertNotIn("x-school-id", headers)
            self.assertNotIn("authorization", headers)
            self.assertNotIn("cookie", headers)
            if request.get_method() == "POST":
                self.assertEqual(target.path, probe.RESET_PATH)
                self.assertEqual(request.data, b"{}")
            else:
                self.assertEqual(target.path, probe.HEALTH_PATH)
                self.assertNotIn("x-admin-ops-secret", headers)
        self.assertEqual(opener.requests[1].get_header("X-admin-ops-secret"), NEW)
        self.assertEqual(opener.requests[2].get_header("X-admin-ops-secret"), OLD)

    def test_wrong_runtime_never_receives_credentials(self):
        for change in ({"env": "prod"}, {"build_sha": "b" * 40},
                       {"artifact_build_sha": "b" * 40}, {"db": "error"}, {"ok": False}):
            with self.subTest(change=change):
                opener = Opener(Response(200, health(**change)))
                result = probe.probe(SHA, OLD, NEW, opener=opener)
                self.assertEqual(result["reset_credential_probe"], "BLOCKED")
                self.assertEqual(len(opener.requests), 1)

    def test_disabled_gate_or_wrong_validation_stops_before_historical_value(self):
        for status, body in ((403, {"detail": "Not allowed outside dev"}),
                             (403, {"detail": "Forbidden"}),
                             (400, {"detail": "Missing something else"})):
            with self.subTest(status=status, body=body):
                opener = Opener(Response(200, health()), Response(status, body))
                result = probe.probe(SHA, OLD, NEW, opener=opener)
                self.assertEqual(result["reset_credential_probe"], "BLOCKED")
                self.assertEqual(result["checks"]["historical_reset"], "NOT_TESTED")
                self.assertEqual(len(opener.requests), 2)

    def test_generic_historical_403_is_not_retirement_proof(self):
        for body in ({"detail": "Not allowed outside dev"}, {"error": "Forbidden"}, None):
            result = probe.probe(SHA, OLD, NEW,
                                 opener=self.passing_opener(old_response=Response(403, body)))
            self.assertEqual(result["reset_credential_probe"], "BLOCKED")

    def test_historical_acceptance_fails(self):
        result = probe.probe(SHA, OLD, NEW, opener=self.passing_opener(
            old_response=Response(400, probe.MISSING_SCHOOL)))
        self.assertEqual(result["reset_credential_probe"], "BLOCKED")

    def test_unexpected_successful_reset_response_is_never_read(self):
        response = Response(200, {"sensitive": OLD}, forbid_read=True)
        result = probe.probe(SHA, OLD, NEW, opener=self.passing_opener(old_response=response))
        self.assertEqual(result["reset_credential_probe"], "BLOCKED")
        self.assertTrue(response.closed)
        self.assertEqual(response.read_sizes, [])

    def test_runtime_movement_or_lost_health_blocks(self):
        for body in (health(build_sha="b" * 40), health(db="error")):
            result = probe.probe(SHA, OLD, NEW, opener=self.passing_opener(
                final_health=Response(200, body)))
            self.assertEqual(result["reset_credential_probe"], "BLOCKED")

    def test_http_error_validation_responses_are_supported_and_closed(self):
        replacement_body = io.BytesIO(json.dumps(probe.MISSING_SCHOOL).encode())
        retired_body = io.BytesIO(b'{"detail":"Forbidden"}')
        opener = Opener(Response(200, health()),
                        urllib.error.HTTPError(probe.API, 400, "validation", {}, replacement_body),
                        urllib.error.HTTPError(probe.API, 403, "denied", {}, retired_body),
                        Response(200, health()))
        self.assertEqual(probe.probe(SHA, OLD, NEW, opener=opener)["reset_credential_probe"], "PASS")
        self.assertTrue(replacement_body.closed)
        self.assertTrue(retired_body.closed)

    def test_redirect_is_not_followed_or_read(self):
        handler = probe.NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "redirect", {},
                                                  "https://untrusted.invalid"))
        response = Response(302, forbid_read=True)
        opener = Opener(response)
        self.assertEqual(probe.probe(SHA, OLD, NEW, opener=opener)["reset_credential_probe"], "BLOCKED")
        self.assertEqual(len(opener.requests), 1)
        self.assertTrue(response.closed)

    def test_body_limit_and_invalid_json_cannot_pass(self):
        for raw in (b"x" * (probe.MAX_BYTES + 1), b"not-json", b"\xff"):
            response = Response(200, raw=raw)
            result = probe.probe(SHA, OLD, NEW, opener=Opener(response))
            self.assertEqual(result["reset_credential_probe"], "BLOCKED")
            self.assertEqual(response.read_sizes, [probe.MAX_BYTES + 1])
            self.assertTrue(response.closed)

    def test_transport_failure_does_not_leak_exception(self):
        opener = Opener(urllib.error.URLError(OLD))
        result = probe.probe(SHA, OLD, NEW, opener=opener)
        self.assertEqual(result["reset_credential_probe"], "BLOCKED")
        self.assertNotIn(OLD, json.dumps(result))

    def test_invalid_input_never_constructs_network_client(self):
        invalid = [("main", OLD, NEW), ("A" * 40, OLD, NEW),
                   (SHA, None, NEW), (SHA, OLD, "short"), (SHA, NEW, NEW),
                   (SHA, OLD + "\r\n", NEW), (SHA, OLD, NEW + " "),
                   (SHA, OLD, NEW + "\u00e9")]
        with patch.object(probe.urllib.request, "build_opener") as build:
            for expected, retired, replacement in invalid:
                with self.subTest(expected=expected), self.assertRaises(ValueError):
                    probe.probe(expected, retired, replacement)
            build.assert_not_called()

    def test_cli_emits_only_sanitized_receipt(self):
        output = io.StringIO()
        with patch.dict(probe.os.environ, {probe.RETIRED_ENV: OLD, probe.REPLACEMENT_ENV: NEW}), \
             patch.object(probe.urllib.request, "build_opener", return_value=self.passing_opener()), \
             contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(["--expected-runtime-sha", SHA]), 0)
        text = output.getvalue()
        self.assertNotIn(OLD, text)
        self.assertNotIn(NEW, text)
        self.assertNotIn(probe.MISSING_SCHOOL["detail"], text)
        self.assertEqual(json.loads(text)["reset_credential_probe"], "PASS")

    def test_cli_rejects_secret_arguments_without_echoing_them(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as failure:
            probe.main(["--expected-runtime-sha", SHA, "--secret", OLD])
        self.assertEqual(failure.exception.code, 2)
        self.assertNotIn(OLD, output.getvalue())

    def test_ci_runs_contract_only_without_real_operator_credentials(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/azure-classroom-preflight.yml").read_text()
        collector = workflow.split("  collector-tests:", 1)[1].split("  jireh-free-staging-once:", 1)[0]
        self.assertIn("-p test_verify_dev_ops_credential_retirement.py", collector)
        self.assertNotIn("secrets.", collector)
        self.assertNotIn("--expected-runtime-sha", collector)


if __name__ == "__main__":
    unittest.main()
