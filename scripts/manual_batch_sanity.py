#!/usr/bin/env python
"""
Quick sanity checks for batch weight endpoint.
Tests: happy path, bad sum, foreign ID.
"""
import requests
import json

BASE = "http://127.0.0.1:8000"
SCHOOL = "b45b8c5a-6708-4597-aad9-a226627b2962"
SECTION = "044882e0-3405-4542-a237-32f1adf4f047"

# Get token
auth_resp = requests.post(f"{BASE}/api/v1/auth/token/", json={
    "username": "head@crown-demo.local",
    "password": "demo1234"
})
TOKEN = auth_resp.json()["access"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "X-School-Id": SCHOOL,
    "Content-Type": "application/json"
}

# Get existing categories
cats_resp = requests.get(
    f"{BASE}/api/v1/academics/sections/{SECTION}/categories/",
    headers=HEADERS
)
cats = [c for c in cats_resp.json()["categories"] if c["is_active"]]
print(f"Found {len(cats)} active categories: {[c['name'] for c in cats]}\n")

if len(cats) < 4:
    print("❌ Need at least 4 active categories for testing")
    exit(1)

# TEST 1: Happy path (40/30/20/10)
print("=" * 60)
print("TEST 1: Happy path (40/30/20/10)")
print("=" * 60)
payload1 = [
    {"id": cats[0]["id"], "weight_percent": "40.00", "is_active": True},
    {"id": cats[1]["id"], "weight_percent": "30.00", "is_active": True},
    {"id": cats[2]["id"], "weight_percent": "20.00", "is_active": True},
    {"id": cats[3]["id"], "weight_percent": "10.00", "is_active": True},
]
resp1 = requests.put(
    f"{BASE}/api/v1/academics/sections/{SECTION}/categories/weights/",
    headers=HEADERS,
    json=payload1
)
if resp1.status_code == 200:
    print(f"✅ Status: {resp1.status_code} OK")
    result_cats = resp1.json()["categories"]
    print(f"✅ Returned {len(result_cats)} categories")
    for c in result_cats:
        print(f"   - {c['name']}: {c['weight_percent']}%")
else:
    print(f"❌ Status: {resp1.status_code}")
    print(f"   Error: {resp1.json()}")

# TEST 2: Bad sum (40/30/20/5 = 95)
print("\n" + "=" * 60)
print("TEST 2: Bad sum (40/30/20/5 = 95)")
print("=" * 60)
payload2 = [
    {"id": cats[0]["id"], "weight_percent": "40.00", "is_active": True},
    {"id": cats[1]["id"], "weight_percent": "30.00", "is_active": True},
    {"id": cats[2]["id"], "weight_percent": "20.00", "is_active": True},
    {"id": cats[3]["id"], "weight_percent": "5.00", "is_active": True},
]
resp2 = requests.put(
    f"{BASE}/api/v1/academics/sections/{SECTION}/categories/weights/",
    headers=HEADERS,
    json=payload2
)
if resp2.status_code == 400:
    print(f"✅ Status: {resp2.status_code} (correctly rejected)")
    error = resp2.json()
    print(f"✅ Error message: {error}")
else:
    print(f"❌ Status: {resp2.status_code} (should be 400)")
    print(f"   Response: {resp2.json()}")

# TEST 3: Foreign ID (category from another section)
print("\n" + "=" * 60)
print("TEST 3: Foreign ID (fake UUID)")
print("=" * 60)
fake_id = "00000000-0000-0000-0000-000000000000"
payload3 = [
    {"id": cats[0]["id"], "weight_percent": "50.00", "is_active": True},
    {"id": fake_id, "weight_percent": "50.00", "is_active": True},
]
resp3 = requests.put(
    f"{BASE}/api/v1/academics/sections/{SECTION}/categories/weights/",
    headers=HEADERS,
    json=payload3
)
if resp3.status_code == 400:
    print(f"✅ Status: {resp3.status_code} (correctly rejected)")
    error = resp3.json()
    print(f"✅ Error message: {error}")
    if "not found in this section" in str(error).lower():
        print(f"✅ Section scoping validated")
else:
    print(f"❌ Status: {resp3.status_code} (should be 400)")
    print(f"   Response: {resp3.json()}")

print("\n" + "=" * 60)
print("SANITY CHECK SUMMARY")
print("=" * 60)
print(f"Test 1 (happy path): {'✅ PASS' if resp1.status_code == 200 else '❌ FAIL'}")
print(f"Test 2 (bad sum):    {'✅ PASS' if resp2.status_code == 400 else '❌ FAIL'}")
print(f"Test 3 (foreign ID): {'✅ PASS' if resp3.status_code == 400 else '❌ FAIL'}")
