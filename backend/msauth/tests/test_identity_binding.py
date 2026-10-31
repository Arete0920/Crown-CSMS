"""Regression tests for immutable Microsoft session OAuth identity binding."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from core.auth.aad_jwt import MicrosoftIdentityError
from msauth.views import me_view, microsoft_callback


class MicrosoftSessionIdentityBindingTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000201")
        self.object_id = uuid.UUID("00000000-0000-0000-0000-000000000202")
        self.user_id = uuid.UUID("00000000-0000-0000-0000-000000000203")
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000204")

    def _request(self):
        request = self.factory.get(
            "/auth/microsoft/callback/",
            {"state": "expected-state", "code": "synthetic-code"},
        )
        request.session = {"oauth_state": "expected-state"}
        return request

    def _oauth_mocks(self, *, mail="renamed@example.invalid", upn="renamed@example.invalid"):
        exchange = MagicMock()
        exchange.fetch_token.return_value = {"access_token": "synthetic-provider-token"}

        graph = MagicMock()

        def graph_get(url):
            response = MagicMock()
            if url.endswith("/me"):
                response.json.return_value = {
                    "id": str(self.object_id),
                    "mail": mail,
                    "userPrincipalName": upn,
                }
            elif "memberOf" in url:
                response.json.return_value = {"value": [{"id": "group-admin"}]}
            else:
                raise AssertionError(f"Unexpected Graph URL: {url}")
            return response

        graph.get.side_effect = graph_get
        return exchange, graph

    def test_callback_resolves_by_tenant_and_graph_object_id_not_email(self):
        request = self._request()
        exchange, graph = self._oauth_mocks(
            mail="changed-mail@example.invalid",
            upn="changed-upn@example.invalid",
        )
        user = SimpleNamespace(
            pk=self.user_id,
            email="canonical-crown@example.invalid",
            school_id=self.school_id,
        )

        with (
            patch("msauth.views.AZURE_TENANT_ID", str(self.tenant_id)),
            patch("msauth.views.ROLE_GROUP_MAP", {"admin": "group-admin"}),
            patch("msauth.views.OAuth2Session", side_effect=[exchange, graph]),
            patch("msauth.views.get_user_from_claims", return_value=user) as resolve,
            patch("msauth.views.login") as login_mock,
        ):
            response = microsoft_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dash/admin")
        resolve.assert_called_once_with(
            {"tid": str(self.tenant_id), "oid": str(self.object_id)}
        )
        login_mock.assert_called_once_with(request, user)
        self.assertEqual(request.session["crown_display_role"], "admin")
        self.assertNotIn("changed-mail@example.invalid", str(resolve.call_args))

    def test_callback_does_not_mutate_crown_role_from_microsoft_group(self):
        request = self._request()
        exchange, graph = self._oauth_mocks()
        user = SimpleNamespace(
            pk=self.user_id,
            email="canonical-crown@example.invalid",
            school_id=self.school_id,
            roles=SimpleNamespace(),
        )

        with (
            patch("msauth.views.AZURE_TENANT_ID", str(self.tenant_id)),
            patch("msauth.views.ROLE_GROUP_MAP", {"admin": "group-admin"}),
            patch("msauth.views.OAuth2Session", side_effect=[exchange, graph]),
            patch("msauth.views.get_user_from_claims", return_value=user),
            patch("msauth.views.login"),
        ):
            response = microsoft_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(hasattr(user, "role"))
        self.assertEqual(request.session["crown_display_role"], "admin")

    def test_unprovisioned_immutable_identity_is_denied_before_session_login(self):
        request = self._request()
        exchange, graph = self._oauth_mocks()

        with (
            patch("msauth.views.AZURE_TENANT_ID", str(self.tenant_id)),
            patch("msauth.views.ROLE_GROUP_MAP", {"admin": "group-admin"}),
            patch("msauth.views.OAuth2Session", side_effect=[exchange, graph]),
            patch(
                "msauth.views.get_user_from_claims",
                side_effect=MicrosoftIdentityError("not provisioned"),
            ),
            patch("msauth.views.login") as login_mock,
        ):
            response = microsoft_callback(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {"error": "User not provisioned in CROWN"})
        login_mock.assert_not_called()

    def test_missing_graph_object_id_is_denied_without_identity_lookup(self):
        request = self._request()
        exchange, graph = self._oauth_mocks()

        def graph_get(url):
            response = MagicMock()
            if url.endswith("/me"):
                response.json.return_value = {
                    "mail": "display@example.invalid",
                    "userPrincipalName": "display@example.invalid",
                }
            elif "memberOf" in url:
                response.json.return_value = {"value": [{"id": "group-admin"}]}
            return response

        graph.get.side_effect = graph_get

        with (
            patch("msauth.views.AZURE_TENANT_ID", str(self.tenant_id)),
            patch("msauth.views.ROLE_GROUP_MAP", {"admin": "group-admin"}),
            patch("msauth.views.OAuth2Session", side_effect=[exchange, graph]),
            patch("msauth.views.get_user_from_claims") as resolve,
            patch("msauth.views.login") as login_mock,
        ):
            response = microsoft_callback(request)

        self.assertEqual(response.status_code, 400)
        resolve.assert_not_called()
        login_mock.assert_not_called()

    def test_session_probe_exposes_navigation_hint_not_user_role_attribute(self):
        request = self.factory.get("/auth/me/")
        request.user = SimpleNamespace(
            is_authenticated=True,
            email="crown-user@example.invalid",
            school_id=self.school_id,
            role="should-not-be-used",
        )
        request.session = {"crown_display_role": "teacher"}

        response = me_view(request)
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["role"], "teacher")
        self.assertEqual(payload["school_id"], str(self.school_id))
