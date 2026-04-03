#!/usr/bin/env python
"""Fetch real grades payload from API"""
import requests
import json

BASE = "http://127.0.0.1:8000"

# Login with account from that school
resp = requests.post(f"{BASE}/api/v1/auth/token/", json={"username":"head@crown-demo.local","password":"demo1234"})
token = resp.json().get("access")

if not token:
    print("Login failed")
    print(resp.json())
    exit(1)

school_id = "b45b8c5a-6708-4597-aad9-a226627b2962"
section_id = "044882e0-3405-4542-a237-32f1adf4f047"

headers = {
    "Authorization": f"Bearer {token}",
    "X-School-Id": school_id
}

# Get the grades
resp = requests.get(f"{BASE}/api/v1/gradebook/sections/{section_id}/grades/", headers=headers)

print("="*70)
print("REAL GRADES PAYLOAD (from GET /api/v1/gradebook/sections/<id>/grades/)")
print("="*70)
print(json.dumps(resp.json(), indent=2))
print("="*70)
