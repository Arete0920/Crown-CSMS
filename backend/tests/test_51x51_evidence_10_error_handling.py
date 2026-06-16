"""
Module 010 — Error Handling & Monitoring
Evidence Test File
==================
Proves that Crown2026's error handling and monitoring boundary is:
  1. RequestCorrelationMiddleware is importable and instantiable.
  2. Middleware assigns X-Correlation-ID on every response.
  3. Middleware propagates an existing X-Correlation-ID from request headers.
  4. Middleware works with no authenticated user (anonymous request).
  5. Middleware works when tenant context is absent.
  6. Structured log record contains required keys.
  7. Middleware is registered in Django MIDDLEWARE setting (integration guard).

SHA evidence: tied to current main — see commit history for module-010 wiring commit.
"""

import json
import logging
import uuid

from django.test import TestCase, RequestFactory

from core.observability.middleware import RequestCorrelationMiddleware


class TestModule010MiddlewareUnit(TestCase):
    """Unit tests for RequestCorrelationMiddleware."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_middleware(self, log_records):
        """Return a middleware instance wired to a no-op get_response."""
        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("ok", status=200)

        mw = RequestCorrelationMiddleware(get_response)
        return mw

    # ------------------------------------------------------------------
    # 1. Middleware is importable and instantiable
    # ------------------------------------------------------------------
    def test_middleware_importable(self):
        mw = self._make_middleware([])
        self.assertIsInstance(mw, RequestCorrelationMiddleware)

    # ------------------------------------------------------------------
    # 2. X-Correlation-ID header is set on response
    # ------------------------------------------------------------------
    def test_response_has_correlation_id_header(self):
        mw = self._make_middleware([])
        request = self.factory.get("/api/v1/test/")
        response = mw(request)
        self.assertIn(
            "X-Correlation-ID", response,
            "Response must carry X-Correlation-ID header.",
        )
        cid = response["X-Correlation-ID"]
        self.assertTrue(len(cid) > 0, "X-Correlation-ID must be non-empty.")

    # ------------------------------------------------------------------
    # 3. Existing X-Correlation-ID is propagated from request
    # ------------------------------------------------------------------
    def test_existing_correlation_id_propagated(self):
        mw = self._make_middleware([])
        incoming_cid = str(uuid.uuid4())
        request = self.factory.get("/api/v1/test/", HTTP_X_CORRELATION_ID=incoming_cid)
        response = mw(request)
        self.assertEqual(
            response["X-Correlation-ID"],
            incoming_cid,
            "Middleware must propagate an incoming X-Correlation-ID unchanged.",
        )

    # ------------------------------------------------------------------
    # 4. Anonymous (unauthenticated) request does not raise
    # ------------------------------------------------------------------
    def test_anonymous_request_does_not_raise(self):
        mw = self._make_middleware([])
        request = self.factory.get("/api/v1/test/")
        # No user set — middleware should handle gracefully
        try:
            response = mw(request)
        except Exception as exc:
            self.fail(f"Middleware raised unexpectedly for anonymous request: {exc}")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # 5. Missing tenant context does not raise
    # ------------------------------------------------------------------
    def test_missing_tenant_context_does_not_raise(self):
        mw = self._make_middleware([])
        request = self.factory.get("/api/v1/test/")
        # Explicitly ensure no tenant attr
        if hasattr(request, "tenant"):
            del request.tenant
        try:
            response = mw(request)
        except Exception as exc:
            self.fail(f"Middleware raised unexpectedly with no tenant: {exc}")
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # 6. Structured log record contains required keys
    # ------------------------------------------------------------------
    def test_log_record_contains_required_keys(self):
        log_records = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record.getMessage())

        handler = CapturingHandler()
        logger = logging.getLogger("crown.request")
        old_level = logger.level

        try:
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)

            mw = self._make_middleware(log_records)
            request = self.factory.get("/api/v1/test/")
            mw(request)
        finally:
            logger.setLevel(old_level)
            logger.removeHandler(handler)
        self.assertTrue(
            len(log_records) > 0,
            "Middleware must emit at least one log record.",
        )
        payload = json.loads(log_records[-1])
        for key in ("event", "method", "path", "status_code", "duration_ms", "correlation_id"):
            self.assertIn(key, payload, f"Log record missing required key: {key}")

        self.assertEqual(payload["event"], "http_request")
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["path"], "/api/v1/test/")
        self.assertEqual(payload["status_code"], 200)


class TestModule010MiddlewareSettingsIntegration(TestCase):
    """Integration guard: RequestCorrelationMiddleware must be in MIDDLEWARE."""

    def test_middleware_registered_in_settings(self):
        from django.conf import settings
        self.assertIn(
            "core.observability.middleware.RequestCorrelationMiddleware",
            settings.MIDDLEWARE,
            "RequestCorrelationMiddleware must be listed in settings.MIDDLEWARE.",
        )


class TestModule010MiddlewareCorrelationIdGeneration(TestCase):
    """Verifies correlation ID is unique per request when none is supplied."""

    def setUp(self):
        self.factory = RequestFactory()

    def _get_cid(self):
        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse("ok")

        mw = RequestCorrelationMiddleware(get_response)
        request = self.factory.get("/api/v1/test/")
        response = mw(request)
        return response["X-Correlation-ID"]

    def test_correlation_ids_are_unique_across_requests(self):
        cids = {self._get_cid() for _ in range(5)}
        self.assertEqual(
            len(cids),
            5,
            "Each request without an incoming correlation ID must generate a unique one.",
        )

    def test_correlation_id_is_valid_uuid(self):
        cid = self._get_cid()
        uuid.UUID(cid)  # raises ValueError if invalid
