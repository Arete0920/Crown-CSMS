#!/bin/bash
# Provision CI user on Azure App Service (DEV)
# Usage: CI_PASSWORD="..." source provision_ci_user_dev_azure.sh

set -e

RESOURCE_GROUP="crown-2026-dev-rg"
APP_NAME="crown-api-dev"

if [ -z "$CI_PASSWORD" ]; then
  echo "ERROR: CI_PASSWORD environment variable is required"
  exit 1
fi

echo "Provisioning CI user on $APP_NAME..."

# Create the Python script inline
cat > /tmp/provision_ci.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown2026_config.settings')
django.setup()

from django.contrib.auth.models import User

username = "ci-golden@crown-demo.local"
password = os.environ.get("CI_PASSWORD")

if not password:
    raise ValueError("CI_PASSWORD not set")

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

print(f"CI user: created={created}, id={user.id}")
user.set_password(password)
user.save()
print(f"✅ Password updated")
PYTHON_SCRIPT

# For Azure App Service, use the Kudu API or direct SSH
# This is a reference implementation; actual deployment depends on your auth setup

echo "✅ Provisioning script ready at /tmp/provision_ci.py"
echo "To deploy, use Azure Portal SSH or Kudu console"

