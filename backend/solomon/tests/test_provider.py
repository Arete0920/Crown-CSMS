"""Synthetic transport, cost, privacy and audit boundaries; no paid API calls."""
import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIClient

from audit.models import AuditLog
from core.models import School, UserAccount, UserRole
from solomon.guidance import GuidanceInputError
from solomon.provider import (
    ENDPOINT, MAX_OUTPUT_TOKENS, MAX_RESPONSE_BYTES, ProviderUnavailable,
    build_request, generate, release_configuration, release_fingerprint,
    reserve_request, send_request, validate_result,
)

PATH = "/api/solomon/assistance/"
SELECTION = {"topic": "communications", "human_review_acknowledged": True}
DRAFT = {"title": "General draft", "guidance": "Review this synthetic outline.",
         "steps": ["Check all placeholders."], "draft": "General event: [date]"}
RESPONSE = {"status": "completed", "output": [{"type": "message", "role": "assistant",
            "content": [{"type": "output_text", "text": json.dumps(DRAFT)}]}]}
CONFIG = {"model": "synthetic-model", "key": "synthetic-key", "namespace": "synthetic-project",
          "limit": 2, "quota_url": "rediss://quota.example.invalid:6379/0"}
RELEASE = {
    "CROWN_SOLOMON_EXTERNAL_ENABLED": True, "CROWN_SOLOMON_RELEASE_APPROVED": True,
    "CROWN_SOLOMON_MODEL": CONFIG["model"], "OPENAI_API_KEY": CONFIG["key"],
    "CROWN_SOLOMON_QUOTA_NAMESPACE": CONFIG["namespace"],
    "CROWN_SOLOMON_QUOTA_REDIS_URL": CONFIG["quota_url"],
    "CROWN_SOLOMON_DAILY_REQUEST_LIMIT": CONFIG["limit"],
    "CROWN_SOLOMON_RELEASE_FINGERPRINT": release_fingerprint(CONFIG["model"], CONFIG["limit"]),
    **{f"CROWN_SOLOMON_{name}_REVIEW_REF": "synthetic-review"
       for name in ("CONTRACT", "RETENTION", "EVALUATION", "BUDGET", "CORPUS")},
}


class ProviderBoundaryTests(SimpleTestCase):
    @override_settings(ROOT_URLCONF="crown_api.urls")
    def test_authoritative_route(self):
        from solomon.guidance_views import assistance_view
        self.assertEqual(resolve(PATH).func, assistance_view)

    def test_request_is_source_only_without_storage_tools_or_user_fields(self):
        body = build_request(SELECTION, CONFIG["model"])
        for flag in ("store", "background", "stream"):
            self.assertIs(body[flag], False)
        self.assertEqual(body["tools"], [])
        self.assertEqual(body["tool_choice"], "none")
        self.assertEqual(body["max_output_tokens"], MAX_OUTPUT_TOKENS)
        data = json.loads(body["input"])
        self.assertEqual(set(data), {"topic", "source"})
        self.assertEqual(data["topic"], SELECTION["topic"])
        self.assertIn("[date]", data["source"]["draft"])
        self.assertNotIn(CONFIG["key"], json.dumps(body))
        for field in ("prompt", "student_id", "parent_id", "school_id", "metrics", "attachment", "model", "url"):
            with self.subTest(field=field), self.assertRaises(GuidanceInputError):
                build_request({**SELECTION, field: "private"}, CONFIG["model"])
        with self.assertRaises(GuidanceInputError):
            build_request({**SELECTION, "topic": "strategy"}, CONFIG["model"])

    @override_settings(**RELEASE)
    def test_release_evidence_configuration_and_fingerprint_fail_closed(self):
        self.assertEqual(release_configuration(), CONFIG)
        for field in RELEASE:
            value = False if type(RELEASE[field]) is bool else ""
            with self.subTest(field=field), override_settings(**{field: value}), self.assertRaises(ProviderUnavailable):
                release_configuration()
        for changes in ({"CROWN_SOLOMON_MODEL": "changed-model"},
                        {"CROWN_SOLOMON_DAILY_REQUEST_LIMIT": 3},
                        {"CROWN_SOLOMON_QUOTA_REDIS_URL": "redis://quota.example.invalid"},
                        {"CROWN_SOLOMON_QUOTA_REDIS_URL": "https://quota.example.invalid"},
                        {"CROWN_SOLOMON_QUOTA_REDIS_URL": CONFIG["quota_url"] + "?ssl_cert_reqs=none"}):
            with self.subTest(changes=changes), override_settings(**changes), self.assertRaises(ProviderUnavailable):
                release_configuration()
        with patch("solomon.provider.INSTRUCTIONS", "Changed instructions"):
            with self.assertRaises(ProviderUnavailable):
                release_configuration()

    def test_atomic_shared_quota_is_required_and_never_refunded(self):
        with patch("solomon.provider.redis.Redis.from_url") as factory:
            connection = factory.return_value
            connection.eval.return_value = 1
            reserve_request(CONFIG)
            factory.assert_called_once_with(CONFIG["quota_url"], ssl_cert_reqs="required",
                                            socket_connect_timeout=2, socket_timeout=2)
            args = connection.eval.call_args.args
            self.assertEqual(args[1], 1)
            self.assertTrue(args[2].startswith("solomon:external:synthetic-project:"))
            self.assertEqual(args[3], 2)
            connection.close.assert_called_once()
            connection.eval.return_value = 0
            with patch("solomon.provider.send_request") as send, self.assertRaises(ProviderUnavailable):
                generate(SELECTION, CONFIG)
            send.assert_not_called()
            connection.eval.side_effect = RuntimeError("synthetic-secret")
            with self.assertRaises(ProviderUnavailable) as failure:
                reserve_request(CONFIG)
            self.assertNotIn("synthetic-secret", str(failure.exception))

    def test_fixed_transport_has_tls_no_redirect_proxy_or_retry_and_bounded_response(self):
        with patch("solomon.provider.requests.Session") as factory:
            session = factory.return_value.__enter__.return_value
            response = session.post.return_value.__enter__.return_value
            response.status_code = 200
            response.headers = {"Content-Type": "application/json"}
            response.raw.read.return_value = json.dumps(RESPONSE).encode()
            self.assertEqual(send_request({}, CONFIG["key"]), RESPONSE)
            self.assertIs(session.trust_env, False)
            args, kwargs = session.post.call_args
            self.assertEqual(args, (ENDPOINT,))
            self.assertFalse(kwargs["allow_redirects"])
            self.assertTrue(kwargs["verify"])
            self.assertEqual(kwargs["timeout"], (3, 10))
            response.raw.read.assert_called_once_with(MAX_RESPONSE_BYTES + 1, decode_content=True)
            for status in (302, 401, 429, 500):
                response.status_code = status
                with self.subTest(status=status), self.assertRaises(ProviderUnavailable):
                    send_request({}, CONFIG["key"])
            response.status_code = 200
            response.raw.read.return_value = b"x" * (MAX_RESPONSE_BYTES + 1)
            with self.assertRaises(ProviderUnavailable):
                send_request({}, CONFIG["key"])

    def test_refusals_incomplete_tool_output_and_invalid_shapes_are_rejected(self):
        self.assertEqual(validate_result(RESPONSE), DRAFT)
        malformed = [None, [], {}, {**RESPONSE, "status": "incomplete"},
                     {**RESPONSE, "output": [{"type": "function_call"}]},
                     {**RESPONSE, "output": [{"type": "message", "role": "assistant",
                       "content": [{"type": "refusal", "refusal": "No"}]}]}]
        for extra in ({"title": "x" * 151}, {"guidance": ""}, {"steps": ["x"] * 7},
                      {"steps": [True]}, {"draft": {}}, {"source_url": "unsafe"}):
            malformed.append({**RESPONSE, "output": [{"type": "message", "role": "assistant",
                              "content": [{"type": "output_text", "text": json.dumps({**DRAFT, **extra})}]}]})
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ProviderUnavailable):
                validate_result(value)


@override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_GUIDANCE_ENABLED=True,
                   CROWN_SOLOMON_EXTERNAL_ENABLED=True, ROOT_URLCONF="solomon.urls")
class AssistanceApiTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic A")
        self.other_school = School.objects.create(name="Synthetic B")
        self.user = UserAccount.objects.create_user(username="synthetic-provider-teacher",
                    email="teacher@example.invalid", school=self.school)
        UserRole.objects.create(user=self.user, school=self.school, role_code="TEACHER")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def post(self, data=None, **kwargs):
        return self.client.post(PATH, SELECTION if data is None else data, format="json", **kwargs)

    def test_generated_result_has_provenance_and_metadata_only_audit(self):
        with patch("solomon.guidance_views.release_configuration", return_value=CONFIG), \
                patch("solomon.guidance_views.generate", return_value=DRAFT) as generator:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["generated_by_ai"])
        self.assertTrue(response.data["human_review_required"])
        self.assertEqual(response.data["mode"], "generated_guidance")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response.data["release_fingerprint"], RELEASE["CROWN_SOLOMON_RELEASE_FINGERPRINT"])
        generator.assert_called_once_with(SELECTION, CONFIG)
        events = list(AuditLog.objects.filter(model="solomon").order_by("id"))
        self.assertEqual({event.action for event in events},
                         {"solomon.assistance.requested", "solomon.assistance.completed"})
        completed = next(event for event in events if event.action.endswith("completed"))
        self.assertEqual(len(completed.metadata["output_digest"]), 64)
        for event in events:
            self.assertNotIn(DRAFT["guidance"], json.dumps(event.metadata))
            self.assertNotIn(CONFIG["key"], json.dumps(event.metadata))

    def test_unapproved_release_and_transport_failure_show_curated_fallback(self):
        with override_settings(CROWN_SOLOMON_RELEASE_APPROVED=False), \
                patch("solomon.provider.send_request") as send:
            response = self.post()
        send.assert_not_called()
        self.assertFalse(response.data["generated_by_ai"])
        self.assertEqual(response.data["external_ai_status"], "unavailable_showing_curated")
        with patch("solomon.guidance_views.release_configuration", return_value=CONFIG), \
                patch("solomon.guidance_views.generate", side_effect=ProviderUnavailable):
            self.assertEqual(self.post().data["mode"], "curated_guidance")

    def test_all_feature_flags_close_endpoint(self):
        for flag in ("CROWN_SOLOMON_API_ENABLED", "CROWN_SOLOMON_GUIDANCE_ENABLED", "CROWN_SOLOMON_EXTERNAL_ENABLED"):
            with override_settings(**{flag: False}), patch("solomon.guidance_views.generate") as generator:
                self.assertEqual(self.post().status_code, 404)
            generator.assert_not_called()

    def test_cross_tenant_student_and_anonymous_requests_never_generate(self):
        with patch("solomon.guidance_views.generate") as generator:
            self.assertEqual(self.post(HTTP_X_SCHOOL_ID=str(self.other_school.pk)).status_code, 404)
            UserRole.objects.create(user=self.user, school=self.school, role_code="STUDENT")
            self.assertEqual(self.post().status_code, 404)
            self.client.force_authenticate(None)
            self.assertIn(self.post().status_code, (401, 403))
        generator.assert_not_called()

    def test_sensitive_extra_strategy_query_and_upload_are_rejected(self):
        with patch("solomon.guidance_views.generate") as generator:
            self.assertEqual(self.post({**SELECTION, "prompt": "synthetic-private"}).status_code, 400)
            self.assertEqual(self.post({**SELECTION, "topic": "strategy"}).status_code, 400)
            self.assertEqual(self.client.post(PATH + "?prompt=private", SELECTION, format="json").status_code, 400)
            self.assertEqual(self.client.post(PATH, SELECTION).status_code, 415)
        generator.assert_not_called()
        self.assertFalse(AuditLog.objects.filter(model="solomon").exists())

    def test_initial_audit_failure_prevents_transport(self):
        with patch("solomon.guidance_views.AuditLog.objects.create", side_effect=RuntimeError("synthetic-secret")), \
                patch("solomon.guidance_views.generate") as generator:
            response = self.post()
        self.assertEqual(response.status_code, 503)
        generator.assert_not_called()
        self.assertNotIn("synthetic-secret", str(response.data))

    def test_completion_audit_failure_withholds_generated_output(self):
        with patch("solomon.guidance_views.AuditLog.objects.create", side_effect=[MagicMock(), RuntimeError("secret")]), \
                patch("solomon.guidance_views.release_configuration", return_value=CONFIG), \
                patch("solomon.guidance_views.generate", return_value=DRAFT):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(DRAFT["guidance"], str(response.data))
