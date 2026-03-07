#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from django.urls import resolve, Resolver404

test_path = '/api/v1/academics/sections/044882e0-3405-4542-a237-32f1adf4f047/categories/weights/'

try:
    match = resolve(test_path)
    print(f"✅ Route exists!")
    print(f"   Resolves to: {match.func.__name__}")
    print(f"   View module: {match.func.__module__}")
except Resolver404 as e:
    print(f"❌ Route NOT FOUND: {e}")
