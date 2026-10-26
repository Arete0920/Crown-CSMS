"""Offline contracts for the no-credential, read-only DEV owner precheck."""

import io
import json
from pathlib import Path
from email.message import Message
import unittest
import urllib.error

import verify_dev_owner_runtime as runtime


SHA = "a" * 40


class FakeResponse(io.BytesIO):
    def __init__(self, data=b"", *, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value


class FakeOpener:
    def __init__(self, *, health=None, frontend=None, status_map=None, cors_headers=None):
        self.calls = []
        self.health = health or {"ok": True, "db": "ok", "env": "dev", "build_sha": SHA,
                                 "artifact_build_sha": SHA}
        self.frontend = frontend or {"build_sha": SHA}
        self.status_map = status_map or {}
        self.cors_headers = cors_headers or {
            "Access-Control-Allow-Origin": runtime.PREVIEW,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "content-type, authorization",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        }

    def open(self, request, timeout):
        self.calls.append((request.full_url, request.get_method(), dict(request.header_items()), timeout))
        if request.get_method() == "OPTIONS":
            return FakeResponse(status=204, headers=self.cors_headers)
        path = request.full_url
        if path in self.status_map:
            status = self.status_map[path]
            if status != 200:
                raise urllib.error.HTTPError(path, status, "Private", {}, None)
        if path == runtime.API + "/api/health/":
            return FakeResponse(json.dumps(self.health).encode())
        if path == runtime.PREVIEW + "/build.json":
            return FakeResponse(json.dumps(self.frontend).encode())
        raise AssertionError(f"Unexpected unconfigured request: {path}")


def safe_opener(**overrides):
    return FakeOpener(status_map={
        runtime.API + "/api/platform/overview": 403,
        runtime.API + "/api/platform/schools/list": 401,
    }, **overrides)


class OwnerRuntimePrecheckTests(unittest.TestCase):
    def test_matching_source_denial_and_cors_still_do_not_claim_acceptance(self):
        client = safe_opener()
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["precheck"], "PASS")
        self.assertEqual(result["overall_release_certification"], "NOT_VERIFIED")
        self.assertEqual(result["owner_console_authenticated_acceptance"], "NOT_TESTED")
        self.assertEqual(result["school_provisioning_execution"], "NOT_TESTED")
        self.assertEqual(len(client.calls), 5)
        for url, method, headers, timeout in client.calls:
            self.assertIn(method, ("GET", "OPTIONS"))
            self.assertEqual(timeout, runtime.TIMEOUT_SECONDS)
            self.assertTrue(url.startswith("https://"))
            self.assertNotIn("Authorization", headers)
            self.assertNotIn("Cookie", headers)
        self.assertNotIn("password", json.dumps(result).lower())

    def test_stale_backend_is_blocked_even_if_health_is_200(self):
        client = safe_opener(health={"ok": True, "db": "ok", "build_sha": "b" * 40,
                                     "artifact_build_sha": SHA, "secret": "DO_NOT_LOG"})
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["precheck"], "BLOCKED")
        self.assertEqual(result["checks"]["backend_build_sha"], "MISMATCH")
        self.assertNotIn("DO_NOT_LOG", json.dumps(result))

    def test_no_owner_authority_is_exposed_anonymously(self):
        client = safe_opener()
        client.status_map[runtime.API + "/api/platform/overview"] = 200
        # A public 200 is not denied even if a test happens to return malformed data.
        def client_open(request, timeout):
            if request.full_url == runtime.API + "/api/platform/overview" and request.get_method() == "GET":
                return FakeResponse(b"SENSITIVE_DATA")
            return FakeOpener.open(client, request, timeout)
        client.open = client_open
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["anonymous_overview"], "EXPOSED")
        self.assertEqual(result["precheck"], "BLOCKED")
        self.assertNotIn("SENSITIVE_DATA", json.dumps(result))

    def test_wrong_environment_fails_even_with_matching_build_and_db(self):
        client = safe_opener(health={"ok": True, "db": "ok", "env": "production",
                                     "build_sha": SHA, "artifact_build_sha": SHA})
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["backend_environment"], "NOT_VERIFIED")
        self.assertEqual(result["precheck"], "BLOCKED")

    def test_owner_probes_never_read_response_bodies(self):
        class StatusOnlyResponse(FakeResponse):
            def read(self, *args, **kwargs):
                raise AssertionError("Owner probe must inspect status only")

        for path, check in (
            ("/api/platform/overview", "anonymous_overview"),
            ("/api/platform/schools/list", "anonymous_school_directory"),
        ):
            for status in (200, 204, 302, 401, 403, 500):
                with self.subTest(path=path, status=status):
                    client = safe_opener()
                    response = StatusOnlyResponse(status=status)

                    def client_open(request, timeout):
                        if request.full_url == runtime.API + path and request.get_method() == "GET":
                            return response
                        return FakeOpener.open(client, request, timeout)

                    client.open = client_open
                    result = runtime.probe(SHA, opener=client)
                    expected = (
                        "DENIED" if status in (401, 403)
                        else "EXPOSED" if status == 200 else "NOT_VERIFIED"
                    )
                    self.assertEqual(result["checks"][check], expected)
                    self.assertEqual(result["precheck"], "PASS" if expected == "DENIED" else "BLOCKED")
                    self.assertTrue(response.closed)

    def test_frontend_mismatch_and_invalid_cors_block(self):
        client = safe_opener(frontend={"build_sha": "b" * 40}, cors_headers={
            "Access-Control-Allow-Origin": "https://unapproved.example",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "authorization",
        })
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["dev_preview_build_sha"], "MISMATCH")
        self.assertEqual(result["checks"]["dev_preview_cors"], "NOT_VERIFIED")
        self.assertEqual(result["precheck"], "BLOCKED")

    def test_cors_must_allow_get_not_just_origin_credentials_and_headers(self):
        client = safe_opener(cors_headers={
            "Access-Control-Allow-Origin": runtime.PREVIEW,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "authorization",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
        })
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["dev_preview_cors"], "NOT_VERIFIED")
        self.assertEqual(result["precheck"], "BLOCKED")

        # Header tokens are case-insensitive; an explicit GET restores readiness.
        client.cors_headers["Access-Control-Allow-Methods"] = "post, gEt"
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["dev_preview_cors"], "READY")
        self.assertEqual(result["precheck"], "PASS")

    def test_unavailable_and_redirect_are_blocked_without_following(self):
        client = safe_opener()
        client.status_map[runtime.API + "/api/health/"] = 302
        client.status_map[runtime.PREVIEW + "/build.json"] = 503
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["precheck"], "BLOCKED")
        self.assertEqual(result["checks"]["backend_build_sha"], "UNAVAILABLE")
        self.assertIsNone(runtime.NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.example/"))

    def test_oversize_and_bad_json_cannot_be_misinterpreted_as_healthy(self):
        client = safe_opener()
        def client_open(request, timeout):
            if request.full_url == runtime.API + "/api/health/":
                return FakeResponse(b"A" * (runtime.MAX_BYTES + 1))
            return FakeOpener.open(client, request, timeout)
        client.open = client_open
        result = runtime.probe(SHA, opener=client)
        self.assertEqual(result["checks"]["backend_build_sha"], "UNAVAILABLE")
        self.assertEqual(result["checks"]["backend_database"], "NOT_VERIFIED")
        self.assertEqual(result["precheck"], "BLOCKED")

    def test_workflow_is_manual_readonly_unprivileged_and_main_only(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    '.github/workflows/azure-classroom-preflight.yml').read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('  push:', workflow)  # existing preflight retains normal triggers
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("dev-owner-runtime-precheck:", workflow)
        self.assertIn("inputs.dev_owner_runtime_precheck == true", workflow)
        self.assertIn("inputs.dev_owner_runtime_precheck != true", workflow)
        self.assertIn('contents: read', workflow)
        owner_job = workflow.split("  dev-owner-runtime-precheck:", 1)[1].split("  azure-inventory:", 1)[0]
        for prohibited in ('id-token: write', 'secrets.', 'azure/login@',
                           'az webapp', 'database_url:', 'POST /api/'):
            self.assertNotIn(prohibited, owner_job)
        self.assertIn('verify_dev_owner_runtime.py --expected-sha', owner_job)

    def test_only_full_lowercase_commit_shas_are_allowed(self):
        for sha in ("", "main", "a" * 7, "A" * 40, "a" * 39 + "\n"):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                runtime.probe(sha, opener=safe_opener())


if __name__ == "__main__":
    unittest.main()
