#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.urls import resolve, Resolver404

test_url = '/api/v1/academics/sections/044882e0-3405-4542-a237-32f1adf4f047/categories/weights/'

print(f"Testing URL: {test_url}\n")

try:
    match = resolve(test_url)
    print("SUCCESS: Route resolves!")
    print(f"  View function: {match.func}")
    print(f"  View name: {match.view_name}")
    print(f"  URL name: {match.url_name}")
    print(f"  Kwargs: {match.kwargs}")
    
    # Try to get the actual view function
    if hasattr(match.func, '__name__'):
        print(f"  Function __name__: {match.func.__name__}")
    if hasattr(match.func, 'view_class'):
        print(f"  View class: {match.func.view_class}")
    if hasattr(match.func, 'cls'):
        print(f"  Class: {match.func.cls}")
        
except Resolver404 as e:
    print(f"ERROR: Route NOT FOUND")
    print(f"  Error: {e}")
