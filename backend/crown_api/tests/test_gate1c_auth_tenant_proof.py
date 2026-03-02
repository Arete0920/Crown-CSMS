# backend/crown_api/tests/test_gate1c_auth_tenant_proof.py
"""
Gate 1C: Tests for auth hardening, tenant enforcement, and whoami proof.
"""
import uuid
from django.test import TestCase, Client
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import School
from django.conf import settings

User = get_user_model()


class Gate1CAuthProofTestCase(TestCase):
    """Test default-deny auth and whoami proof endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(
            id=uuid.uuid4(),
            name="Test School"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="testpass123"
        )
        self.user.school = self.school
        self.user.save()
    
    def test_whoami_requires_authentication(self):
        """Whoami endpoint requires authentication (default-deny)."""
        response = self.client.get('/api/system/whoami/')
        # DRF IsAuthenticated returns 401 when JWTAuthentication is configured
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
        # UserAccount doesn't have a 'role' field (uses UserRole Many-to-Many)
        # whoami returns None for role if not present
        self.assertIsNone(data['user']['role'])
        # UserAccount has is_staff (from AbstractUser)
        self.assertFalse(data['user']['is_staff'])
    
    def test_whoami_returns_tenant_info(self):
        """Whoami includes resolved tenant from middleware."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/system/whoami/',
            HTTP_X_SCHOOL_ID=str(self.school.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Tenant should be resolved from header (header-wins)
        self.assertEqual(data['tenant']['resolved_school_id'], str(self.school.id))
        self.assertEqual(data['tenant']['resolution_source'], 'header')
        self.assertTrue(data['tenant']['header_present'])
    
    def test_whoami_returns_override_info(self):
        """Whoami includes staff override audit info when header differs from user."""
        # Override detection requires staff user
        self.user.is_staff = True
        self.user.save()
        
        # Create a different school for override test
        other_school = School.objects.create(
            id=uuid.uuid4(),
            name="Other School"
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/api/system/whoami/',
            HTTP_X_SCHOOL_ID=str(other_school.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Override should be captured (staff user with header ≠ user.school_id)
        self.assertEqual(data['override']['school_override_id'], str(other_school.id))
    
    def test_whoami_returns_build_sha(self):
        """Whoami includes build_sha for deployment proof."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/system/whoami/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Build data should be present
        self.assertIsNotNone(data['build']['build_sha'])
        self.assertEqual(data['build']['build_sha'], settings.BUILD_SHA)


class Gate1CTenantGuardTestCase(TestCase):
    """Test TenantRequiredMixin enforcement."""
    
    def setUp(self):
        from rest_framework import viewsets
        from rest_framework.response import Response
        from crown_api.tenant_guards import TenantRequiredMixin
        
        # Create a test viewset with the mixin
        class TestTenantViewSet(TenantRequiredMixin, viewsets.ViewSet):
            def list(self, request):
                # After mixin validation, tenant_school_id should be available
                # or we can safely get it from the request
                school_id = getattr(request, 'tenant_school_id', None)
                return Response({"ok": True, "tenant": str(school_id)})
        
        self.viewset_class = TestTenantViewSet
        self.factory = APIRequestFactory()
        self.school = School.objects.create(
            id=uuid.uuid4(),
            name="Test School"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@test.com",
            password="testpass123"
        )
        self.user.school = self.school
        self.user.save()
    
    def _simulate_middleware(self, request):
        """Simulate what TenantContextMiddleware does."""
        from crown_api.tenant import resolve_tenant_school_id, TENANT_ATTR
        res = resolve_tenant_school_id(request)
        setattr(request, TENANT_ATTR, res.school_id)
        setattr(request, "_tenant_resolution_source", res.source)
        setattr(request, "_tenant_header_present", res.header_present)
    
    def test_tenant_mixin_enforces_tenant_required(self):
        """TenantRequiredMixin raises 400 when tenant missing."""
        # Create a user without a school to test missing tenant
        user_no_school = User.objects.create_user(
            username="noschool",
            email="noschool@test.com",
            password="testpass123"
        )
        # Explicitly set school to None
        user_no_school.school = None
        user_no_school.save()
        
        request = self.factory.get('/test/')
        force_authenticate(request, user=user_no_school)
        self._simulate_middleware(request)
        
        view = self.viewset_class.as_view({'get': 'list'})
        
        # No tenant header and no user.school = should raise 400
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_tenant_mixin_allows_valid_tenant(self):
        """TenantRequiredMixin allows request with valid tenant."""
        request = self.factory.get(
            '/test/',
            HTTP_X_SCHOOL_ID=str(self.school.id)
        )
        force_authenticate(request, user=self.user)
        self._simulate_middleware(request)
        
        view = self.viewset_class.as_view({'get': 'list'})
        
        # Valid tenant header = should succeed
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tenant'], str(self.school.id))


class Gate1CDefaultDenyTestCase(TestCase):
    """Test default-deny auth behavior (DRF IsAuthenticated)."""
    
    def setUp(self):
        from rest_framework.decorators import api_view
        from rest_framework.response import Response
        
        # Create a test view that doesn't explicitly set permissions
        # (should inherit DEFAULT_PERMISSION_CLASSES = IsAuthenticated)
        @api_view(['GET'])
        def test_protected_view(request):
            return Response({"ok": True, "user": str(request.user.id)})
        
        self.protected_view = test_protected_view
        self.factory = APIRequestFactory()
        self.client = APIClient()
    
    def test_drf_view_requires_auth_by_default(self):
        """DRF views require authentication by default (IsAuthenticated)."""
        # This is a framework-level test - we're verifying DRF settings
        # are configured correctly in settings.py
        from django.conf import settings as django_settings
        
        self.assertIn(
            'rest_framework.permissions.IsAuthenticated',
            django_settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
        )
