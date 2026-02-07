#!/usr/bin/env python
"""Get a real grades payload for B2 UX development"""
import requests
import json

BASE = "http://127.0.0.1:8000"

# Login
resp = requests.post(f"{BASE}/api/v1/auth/token/", json={"username": "head@crown-demo.local", "password": "demo1234"})
token = resp.json()["access"]
school_id = "7d965a83-e714-413d-86ba-776c4176b50f"

headers = {
    "Authorization": f"Bearer {token}",
    "X-School-Id": school_id
}

# Get sections
sections_resp = requests.get(f"{BASE}/api/v1/gradebook/sections/", headers=headers)
sections = sections_resp.json().get("results", [])

print(f"Found {len(sections)} sections")

if sections:
    section_id = sections[0]["id"]
    print(f"\nFetching grades for section {section_id}...")
    
    # Get grades
    grades_resp = requests.get(f"{BASE}/api/v1/gradebook/sections/{section_id}/grades/", headers=headers)
    
    print(f"\n{'='*60}")
    print("GRADES PAYLOAD (for B2 UX):")
    print(f"{'='*60}")
    print(json.dumps(grades_resp.json(), indent=2))
    print(f"{'='*60}")
    print(f"\nStatus: {grades_resp.status_code}")
else:
    print("\n⚠️  No sections found. Need to seed gradebook data.")
    print("Run: python manage.py seed_gradebook_demo")
