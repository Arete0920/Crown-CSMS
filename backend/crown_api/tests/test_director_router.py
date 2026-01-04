"""
Smoke tests for Director Router

These tests prevent regression of the core routing logic.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sessions.middleware import SessionMiddleware
from crown_api.views import director_router
from core.models import UserAccount


class DirectorRouterTests(TestCase):
    """Test Director Router routing logic"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    def _add_session(self, request):
        """Helper to add session support to request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        return request
    
    def test_anonymous_redirects_to_login(self):
        """Anonymous users should be redirected to login"""
        request = self.factory.get('/director/')
        request.user = AnonymousUser()
        request = self._add_session(request)
        
        response = director_router(request)
        
        # @login_required should redirect
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_admissions_persona_routes_to_admissions(self):
        """User with admissions persona should route to /director/admissions/"""
        request = self.factory.get('/director/')
        request.user = self.user
        request = self._add_session(request)
        
        # Set demo persona
        request.session['demo_persona'] = 'admissions_director'
        
        response = director_router(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/director/admissions/')
    
    def test_aid_persona_routes_to_aid(self):
        """User with financial aid persona should route to /director/aid/"""
        request = self.factory.get('/director/')
        request.user = self.user
        request = self._add_session(request)
        
        # Set demo persona
        request.session['demo_persona'] = 'financial_aid_director'
        
        response = director_router(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/director/aid/')
    
    def test_group_based_routing(self):
        """User in Django group should be routed based on group name"""
        request = self.factory.get('/director/')
        request.user = self.user
        request = self._add_session(request)
        
        # Add user to group
        group = Group.objects.create(name='Admissions Director')
        self.user.groups.add(group)
        
        response = director_router(request)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/director/admissions/')
    
    def test_unknown_persona_returns_403(self):
        """User with unknown persona should get 403"""
        request = self.factory.get('/director/')
        request.user = self.user
        request = self._add_session(request)
        
        # Set unknown persona
        request.session['demo_persona'] = 'unknown_role'
        
        response = director_router(request)
        
        self.assertEqual(response.status_code, 403)
    
    def test_persona_normalization(self):
        """Persona values should be normalized (lowercase, underscores)"""
        request = self.factory.get('/director/')
        request.user = self.user
        request = self._add_session(request)
        
        # Test various formats that should normalize to 'admissions_director'
        for persona_variant in ['ADMISSIONS_DIRECTOR', 'Admissions Director', ' admissions_director ']:
            request.session['demo_persona'] = persona_variant
            response = director_router(request)
            
            # Should still route correctly after normalization
            self.assertEqual(response.status_code, 302, 
                           f"Failed for persona variant: {persona_variant}")
