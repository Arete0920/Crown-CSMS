#!/usr/bin/env python
"""Check user school_id"""
import os
import logging
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from django.contrib.auth import get_user_model


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

User = get_user_model()
u = User.objects.filter(email='head@crown-demo.local').first()
logger.info('User found: %s', u is not None)
logger.info('School ID: %s', u.school_id if u else None)
