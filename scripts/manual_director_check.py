#!/usr/bin/env python
import os
import sys
import django
import json
from urllib.parse import urlencode

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from crown_api.director_views import director_dashboard

# Create request
factory = APIRequestFactory()
school_id = "852e31bc-d953-48c5-b081-98d27469d634"
year_id = "a3e4bc0c-f0db-481b-b5e4-9ec86d45f50a"

request = factory.get(f'/api/director/dashboard/?school_id={school_id}&year_id={year_id}')
request.user = None  # AnonymousUser - AllowAny permission should work

# Call the view
try:
    response = director_dashboard(request)
    print(f"Status: {response.status_code}")
    print(f"Data: {json.dumps(response.data, indent=2, default=str)}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
