# backend/crown_api/tests/test_gate1c_auth_tenant_proof.py
"""
Gate 1C: Tests for auth hardening, tenant enforcement, and whoami proof.
"""
import json
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from core.models import School
from crown_api.system_views import whoami
from crown_api.tenant import TenantContext, bind_tenant_context, build_tenant_context

User = get_user_model()


class Gate1CAuthProofTestCase(TestCase):
    """Test default-deny auth and whoami proof endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()
        self.school = School.objects.create(
            id=uuid.uuid4(),
            name="Test School",
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="testpass123",
        )
        self.user.school = self.school
        self.user.save()

    def test_whoami_requires_authentication(self):
        """Whoami endpoint requires authentication (default-deny)."""
        response = self.client.get('/api/system/whoami/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_whoami_returns_user_info(self):
        """Authenticated whoami returns user data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/system/whoami/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data['ok'])
        self.assertEqual(data['user']['id'], str(self.user.id))
        self.assertEqual(data['user']['email'], self.user.email)
        self.assertIsNone(data['user']['role'])
        self.assertFalse(data['user']['is_staff'])

    def test_whoami_returns_tenant_info(self):
        """Whoami includes resolved tenant from middleware."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/system/whoami/',
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['tenant']['resolved_school_id'], str(self.school.id))
        self.assertEqual(data['tenant']['resolution_source'], 'header')
        self.assertTrue(data['tenant']['header_present'])

    def test_whoami_returns_override_info(self):
        """Whoami includes staff override audit info when header differs from user."""
        self.user.is_staff = True
        self.user.save()
        other_school = School.objects.create(
            id=uuid.uuid4(),
            name="Other School",
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/system/whoami/',
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['override']['school_override_id'], str(other_school.id))

    def test_whoami_returns_build_sha(self):
        """Whoami includes build_sha for deployment proof."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/system/whoami/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIsNotNone(data['build']['build_sha'])
        self.assertEqual(data['build']['build_sha'], settings.BUILD_SHA)

    def test_whoami_reads_canonical_context_not_conflicting_legacy_aliases(self):
        """Canonical request context controls whoami proof output during alias retirement."""
        other_school = School.objects.create(name="Legacy Alias School")
        request = self.factory.get('/api/system/whoami/')
        force_authenticate(request, user=self.user)
        request.crown_tenant = TenantContext(
            school_id=self.school.id,
            school=self.school,
            source='header',
            header_present=True,
            principal_school_id=self.school.id,
            override_requested=False,
            override_authorized=False,
            actor_type='drf_force',
        )
        request.tenant_school_id = other_school.id
        request._tenant_resolution_source = 'legacy-alias'
        request._tenant_header_present = False
        request._crown_school_override_id = other_school.id

        response = whoami(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(data['tenant']['resolved_school_id'], str(self.school.id))
        self.assertEqual(data['tenant']['resolution_source'], 'header')
        self.assertTrue(data['tenant']['header_present'])
        self.assertIsNone(data['override']['school_override_id'])

    def test_whoami_override_comes_from_canonical_authorization(self):
        """Authorized canonical override is reported without reading the legacy override alias."""
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        other_school = School.objects.create(name="Canonical Override School")
        request = self.factory.get('/api/system/whoami/')
        force_authenticate(request, user=self.user)
        request.crown_tenant = TenantContext(
            school_id=other_school.id,
            school=other_school,
            source='header',
            header_present=True,
            principal_school_id=self.school.id,
            override_requested=True,
            override_authorized=True,
            actor_type='drf_force',
        )
        request._crown_school_override_id = self.school.id

        response = whoami(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)

        self.assertEqual(data['tenant']['resolved_school_id'], str(other_school.id))
        self.assertEqual(data['override']['school_override_id'], str(other_school.id))


class Gate1CTenantGuardTestCase(TestCase):
    """Test TenantRequiredMixin enforcement."""

    def setUp(self):
        from rest_framework import viewsets
        from rest_framework.response import Response
        from crown_api.tenant_guards import TenantRequiredMixin

        class TestTenantViewSet(TenantRequiredMixin, viewsets.ViewSet):
            def list(self, request):
                school_id = getattr(request, 'tenant_school_id', None)
                return Response({"ok": True, "tenant": str(school_id)})

        self.viewset_class = TestTenantViewSet
        self.factory = APIRequestFactory()
        self.school = School.objects.create(
            id=uuid.uuid4(),
            name="Test School",
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="testpass123",
        )
        self.user.school = self.school
        self.user.save()

    @staticmethod
    def _simulate_middleware(request):
        """Bind the same canonical context and compatibility aliases as middleware."""
        bind_tenant_context(request, build_tenant_context(request))

    def test_tenant_mixin_enforces_tenant_required(self):
        """TenantRequiredMixin raises 400 when tenant missing."""
        user_no_school = User.objects.create_user(
            username="noschool",
            email="noschool@test.com",
            password="testpass123",
        )
        user_no_school.school = None
        user_no_school.save()

        request = self.factory.get('/test/')
        force_authenticate(request, user=user_no_school)
        self._simulate_middleware(request)

        view = self.viewset_class.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_mixin_allows_valid_tenant(self):
        """TenantRequiredMixin allows request with valid tenant."""
        request = self.factory.get(
            '/test/',
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        force_authenticate(request, user=self.user)
        self._simulate_middleware(request)

        view = self.viewset_class.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tenant'], str(self.school.id))
        self.assertEqual(request.crown_tenant.school_id, self.school.id)


class Gate1CDefaultDenyTestCase(TestCase):
    """Test default-deny auth behavior (DRF IsAuthenticated)."""

    def setUp(self):
        from rest_framework.decorators import api_view
        from rest_framework.response import Response

        @api_view(['GET'])
        def test_protected_view(request):
            return Response({"ok": True, "user": str(request.user.id)})

        self.protected_view = test_protected_view
        self.factory = APIRequestFactory()
        self.client = APIClient()

    def test_drf_view_requires_auth_by_default(self):
        """DRF views require authentication by default (IsAuthenticated)."""
        from django.conf import settings as django_settings

        self.assertIn(
            'rest_framework.permissions.IsAuthenticated',
            django_settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'],
        )
