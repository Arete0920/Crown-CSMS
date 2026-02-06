#!/usr/bin/env python
"""Simulate UI test: login, fetch sections, fetch grades for seeded section, verify payload"""
import requests
import json

BASE_API = "http://127.0.0.1:8000"
SEEDED_SECTION_ID = "044882e0-3405-4542-a237-32f1adf4f047"

# Step 1: Login
print("=" * 70)
print("STEP 1: LOGIN")
print("=" * 70)
resp = requests.post(
    f"{BASE_API}/api/v1/auth/token/",
    json={"username": "head@crown-demo.local", "password": "demo1234"}
)
assert resp.status_code == 200, f"Login failed: {resp.status_code}"
token = resp.json().get("access")
school_id = "b45b8c5a-6708-4597-aad9-a226627b2962"
print(f"✓ Token received: {token[:30]}...")
print(f"✓ School ID: {school_id}")

headers = {
    "Authorization": f"Bearer {token}",
    "X-School-Id": school_id
}

# Step 2: Fetch sections (like frontend does on mount)
print("\n" + "=" * 70)
print("STEP 2: FETCH SECTIONS (simulating frontend UI load)")
print("=" * 70)
resp = requests.get(f"{BASE_API}/api/v1/gradebook/sections/", headers=headers)
assert resp.status_code == 200, f"Sections failed: {resp.status_code}"
sections_data = resp.json()
sections = sections_data if isinstance(sections_data, list) else sections_data.get("results", [])
print(f"✓ Status: 200")
print(f"✓ Sections count: {len(sections)}")
if sections and isinstance(sections[0], dict):
    section_ids = [s.get("id") for s in sections]
    print(f"✓ Section IDs: {section_ids[:3]}...")
else:
    print(f"✓ Sections data structure: {type(sections_data)}")

# Step 3: Fetch grades for the seeded section (user selects section)
print("\n" + "=" * 70)
print("STEP 3: FETCH GRADES FOR SEEDED SECTION (user selects section)")
print("=" * 70)
print(f"Selecting section: {SEEDED_SECTION_ID}")
resp = requests.get(
    f"{BASE_API}/api/v1/gradebook/sections/{SEEDED_SECTION_ID}/grades/",
    headers=headers
)
assert resp.status_code == 200, f"Grades failed: {resp.status_code}"
payload = resp.json()

print(f"✓ Last request name: grades")
print(f"✓ Last request status: 200")
print(f"✓ Assignments count: {len(payload.get('assignments', []))}")
print(f"✓ Rows count: {len(payload.get('rows', []))}")

# Step 4: Verify observable outcomes
print("\n" + "=" * 70)
print("PROOF CHECKLIST")
print("=" * 70)

assignments = payload.get("assignments", [])
rows = payload.get("rows", [])

# Outcome 1: Headers (8 assignments)
assignment_names = [a.get("assignment_name") for a in assignments]
print(f"\n✓ HEADERS (8 assignments):")
for i, name in enumerate(assignment_names, 1):
    print(f"  {i}. {name}")
assert len(assignment_names) == 8, f"Expected 8 assignments, got {len(assignment_names)}"
assert "Assignment 1" in assignment_names
assert "Assignment 6" in assignment_names
assert "Homework 1" in assignment_names
assert "Quiz 1" in assignment_names
print("  ✓ All 8 expected assignments present")

# Outcome 2: One student row
print(f"\n✓ STUDENT ROWS:")
assert len(rows) > 0, "No rows returned"
first_row = rows[0]
student = first_row.get("student", {})
print(f"  Name: {student.get('first_name')} {student.get('last_name')}")
print(f"  Grade: {student.get('grade_level')}")
assert student.get("first_name") == "Ava"
assert student.get("last_name") == "Brooks"
assert student.get("grade_level") == "3"
print("  ✓ Brooks, Ava (Grade 3) confirmed")

# Outcome 3: Two cells match exactly
print(f"\n✓ CELL VALUES (score / possible):")
scores = first_row.get("scores", {})

# Quiz 1: 85 / 100
quiz1 = scores.get("Quiz 1", {})
quiz1_earned = quiz1.get("points_earned")
quiz1_possible = quiz1.get("points_possible")
print(f"  Quiz 1: {quiz1_earned} / {quiz1_possible}")
assert quiz1_earned == 85.0, f"Quiz 1 earned: expected 85.0, got {quiz1_earned}"
assert quiz1_possible == 100.0, f"Quiz 1 possible: expected 100.0, got {quiz1_possible}"
print("    ✓ Quiz 1: 85 / 100 ✓ MATCH")

# Homework 1: 42.5 / 50
hw1 = scores.get("Homework 1", {})
hw1_earned = hw1.get("points_earned")
hw1_possible = hw1.get("points_possible")
print(f"  Homework 1: {hw1_earned} / {hw1_possible}")
assert hw1_earned == 42.5, f"Homework 1 earned: expected 42.5, got {hw1_earned}"
assert hw1_possible == 50.0, f"Homework 1 possible: expected 50.0, got {hw1_possible}"
print("    ✓ Homework 1: 42.5 / 50 ✓ MATCH")

print("\n" + "=" * 70)
print("ALL PROOF CHECKLIST ITEMS PASSED ✓")
print("=" * 70)
print("\nREADY TO COMMIT")
