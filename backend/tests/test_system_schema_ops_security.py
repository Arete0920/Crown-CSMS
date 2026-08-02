from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from crown_api.system_views import diagnose_db_tables_view, fix_schema_drift_view


@override_settings(CROWN_ENV="dev", DJANGO_ENV="")
class SystemSchemaOpsSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(CROWN_OPS_SECRET="", OPS_SECRET="")
    @patch("crown_api.system_views.connection")
    def test_diagnose_fails_closed_when_secret_is_absent(self, connection_mock):
        response = diagnose_db_tables_view(
            self.factory.get("/api/v1/system/diagnose-db-tables/")
        )

        self.assertEqual(response.status_code, 403)
        connection_mock.cursor.assert_not_called()

    @override_settings(CROWN_OPS_SECRET="expected-secret", OPS_SECRET="")
    @patch("crown_api.system_views.connection")
    def test_diagnose_rejects_missing_header(self, connection_mock):
        response = diagnose_db_tables_view(
            self.factory.get("/api/v1/system/diagnose-db-tables/")
        )

        self.assertEqual(response.status_code, 403)
        connection_mock.cursor.assert_not_called()

    @override_settings(CROWN_OPS_SECRET="expected-secret", OPS_SECRET="")
    @patch("crown_api.system_views.connection")
    def test_diagnose_rejects_wrong_secret(self, connection_mock):
        request = self.factory.get(
            "/api/v1/system/diagnose-db-tables/",
            HTTP_X_OPS_SECRET="wrong-secret",
        )

        response = diagnose_db_tables_view(request)

        self.assertEqual(response.status_code, 403)
        connection_mock.cursor.assert_not_called()

    @override_settings(CROWN_OPS_SECRET="expected-secret", OPS_SECRET="")
    @patch("crown_api.system_views.connection")
    def test_diagnose_accepts_exact_secret(self, connection_mock):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [
            (None,),
            ("crown", "127.0.0.1", "PostgreSQL 16"),
        ]
        cursor.fetchall.return_value = []
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor
        connection_mock.cursor.return_value = cursor_context
        request = self.factory.get(
            "/api/v1/system/diagnose-db-tables/",
            HTTP_X_OPS_SECRET="expected-secret",
        )

        response = diagnose_db_tables_view(request)

        self.assertEqual(response.status_code, 200)
        connection_mock.cursor.assert_called_once_with()

    @override_settings(
        CROWN_ENV="production",
        CROWN_OPS_SECRET="expected-secret",
        OPS_SECRET="",
    )
    @patch("crown_api.system_views.connection")
    def test_diagnose_rejects_non_dev_environment(self, connection_mock):
        request = self.factory.get(
            "/api/v1/system/diagnose-db-tables/",
            HTTP_X_OPS_SECRET="expected-secret",
        )

        response = diagnose_db_tables_view(request)

        self.assertEqual(response.status_code, 403)
        connection_mock.cursor.assert_not_called()

    @patch("crown_api.system_views.call_command")
    def test_fix_schema_drift_endpoint_is_retired_and_never_executes_command(self, call_command):
        response = fix_schema_drift_view(
            self.factory.post(
                "/api/v1/system/fix-schema-drift/",
                HTTP_X_OPS_SECRET="expected-secret",
            )
        )

        self.assertEqual(response.status_code, 410)
        self.assertIn(b"retired", response.content.lower())
        call_command.assert_not_called()
