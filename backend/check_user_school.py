#!/usr/bin/env python
"""Check user school_id"""
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.filter(email='head@crown-demo.local').first()
print(f'User found: {u is not None}')
print(f'School ID: {u.school_id if u else None}')
