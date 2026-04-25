#!/usr/bin/env python
"""
Test custom login endpoint
"""

import requests
import json

BACKEND_BASE = 'http://127.0.0.1:8001'
email = 'admissions@bethesda-christian-school.sandbox.example.org'
password = 'SandboxPassword2026!'

endpoint = f'{BACKEND_BASE}/api/auth/login/'

print(f"Testing: {endpoint}")
print(f"Email: {email}")
print("Password: [REDACTED]\n")

try:
    # Try without X-School-Id first
    print("Attempt 1: Without X-School-Id header")
    resp = requests.post(
        endpoint,
        json={'email': email, 'password': password},
        timeout=5
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body: {resp.text[:300]}\n")

    if resp.status_code == 200:
        data = resp.json()
        print("  Token response:")
        print(json.dumps(data, indent=2))

except Exception as e:
    print(f"  Error: {e}")
