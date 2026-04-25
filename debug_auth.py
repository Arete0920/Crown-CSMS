#!/usr/bin/env python
"""
Debug auth endpoint to see actual error response
"""

import requests
import json

BACKEND_BASE = 'http://127.0.0.1:8001'

# Try one actual user
email = 'admissions@bethesda-christian-school.sandbox.example.org'
password = 'SandboxPassword2026!'

print(f"Testing auth with: {email}")
print("Password: [REDACTED]\n")

try:
    resp = requests.post(
        f'{BACKEND_BASE}/api/v1/auth/token/',
        json={'email': email, 'password': password},
        timeout=5
    )

    print(f"Status: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    print(f"Body: {resp.text}\n")

    if resp.status_code == 200:
        data = resp.json()
        print(f"Token response: {json.dumps(data, indent=2)}")
    else:
        print("Error response:")
        try:
            print(json.dumps(resp.json(), indent=2))
        except ValueError:
            print(resp.text)

except Exception as e:
    print(f"Exception: {e}")
