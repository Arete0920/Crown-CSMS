#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from uuid import UUID
from django.test import RequestFactory
from applications.views_admissions import admissions_summary, admissions_drilldown
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request as DRFRequest
import json

# Create mock request
factory = APIRequestFactory()
request = factory.get('/api/v1/admissions/summary/')
request.META['HTTP_X_SCHOOL_ID'] = 'a5351136-98fe-4d48-add0-fa8f62d9ceff'
request.user = None  # We'll skip auth

# Make DRF request
drf_request = DRFRequest(request)
drf_request.user = type('User', (), {'is_authenticated': True})()

# Call endpoint
response = admissions_summary(drf_request)

print('=== Admissions Summary Response ===')
print(json.dumps(response.data, indent=2, default=str))

print('\n=== Drilldown Test (first 5) ===')
request2 = factory.get('/api/v1/admissions/drilldown/?limit=5&offset=0')
request2.META['HTTP_X_SCHOOL_ID'] = 'a5351136-98fe-4d48-add0-fa8f62d9ceff'
drf_request2 = DRFRequest(request2)
drf_request2.user = type('User', (), {'is_authenticated': True})()

response2 = admissions_drilldown(drf_request2)
print(json.dumps(response2.data, indent=2, default=str))
