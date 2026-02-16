#!/usr/bin/env python
"""
[DEPRECATED] Provision CI user (ci-golden@crown-demo.local) on DEV.

⚠️  DO NOT USE THIS SCRIPT.

REASON FOR DEPRECATION:
  1. Script imports django.contrib.auth.models.User, but the application
     uses a custom AUTH_USER_MODEL = 'core.UserAccount' (see settings.py:231).
     This causes the script to create the wrong model type.

  2. CI provisioning is now handled by the /api/v1/system/ensure-ci-user/
     endpoint. See: .github/workflows/dev-smoke-azure-dev.yml:39

  3. Script is not referenced by any active workflow. It is an orphaned
     leftover from an earlier provisioning approach.

RECOMMENDED ALTERNATIVE:
  Use the ensure-ci-user API endpoint:

    curl -X POST "$BASE/api/v1/system/ensure-ci-user/" \
      -H "Authorization: Bearer $DEV_OPS_SECRET" \
      -H "Content-Type: application/json" \
      -d '{"username":"ci-golden@crown-demo.local","password":"..."}'

  See: .github/workflows/dev-smoke-azure-dev.yml for live example.

---

PRESERVED ORIGINAL CODE (for reference only):
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
