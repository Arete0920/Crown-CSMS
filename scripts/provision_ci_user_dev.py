#!/usr/bin/env python
"""
Provision CI user (ci-golden@crown-demo.local) on DEV.

This script must be run in the Django shell or with manage.py.

Environment variables (required):
  CI_PASSWORD: Password for the CI user

Usage:
    cd backend
    CI_PASSWORD="..." python manage.py shell < ../scripts/provision_ci_user_dev.py

Or inline:
    python manage.py shell
    >>> exec(open('../scripts/provision_ci_user_dev.py').read())
"""

import os
from django.contrib.auth.models import User

username = "ci-golden@crown-demo.local"
password = os.environ.get("CI_PASSWORD")

if not password:
    raise ValueError("CI_PASSWORD environment variable is required")

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": "ci@crown-demo.local",
        "first_name": "CI",
        "last_name": "Golden",
        "is_staff": False,
        "is_superuser": False,
    },
)

if not created:
    print(f"User {username} already exists (id={user.id})")
else:
    print(f"Created new user {username} (id={user.id})")

user.set_password(password)
user.save()
print(f"Password set for {username}")
print(f"✅ CI user ready for smoke tests")

