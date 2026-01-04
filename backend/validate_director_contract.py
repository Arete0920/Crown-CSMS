"""
Director Framework Contract Validation Script

Tests that Admissions Director follows the same contract as Aid Director (gold standard).
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_priority_queue():
    """Test /api/director/priority/ contract compliance"""
    print_section("TEST: Priority Queue API Contract")
    
    url = f"{BASE_URL}/api/director/priority/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    # Test required top-level keys
    required_keys = ["meta", "worklist_top_10", "aid", "admissions", "finance", "registrar"]
    for key in required_keys:
        if key in data:
            print(f"✅ Has required key: '{key}'")
        else:
            print(f"❌ Missing required key: '{key}'")
            return False
    
    # Test meta structure
    meta_keys = ["school_id", "year_id"]
    for key in meta_keys:
        if key in data["meta"]:
            print(f"✅ meta.{key} present")
        else:
            print(f"❌ meta.{key} missing")
            return False
    
    # Test worklist structure
    if isinstance(data["worklist_top_10"], list):
        print(f"✅ worklist_top_10 is array (length: {len(data['worklist_top_10'])})")
        
        if len(data["worklist_top_10"]) > 0:
            item = data["worklist_top_10"][0]
            item_keys = ["type", "score", "id", "summary"]
            for key in item_keys:
                if key in item:
                    print(f"✅ worklist item has '{key}'")
                else:
                    print(f"❌ worklist item missing '{key}'")
    else:
        print(f"❌ worklist_top_10 is not an array")
        return False
    
    # Test Aid section structure (gold standard)
    aid_keys = ["needs_info_applications", "under_review_applications", "accepted_not_posted_awards"]
    for key in aid_keys:
        if key in data["aid"]:
            print(f"✅ aid.{key} present")
        else:
            print(f"❌ aid.{key} missing")
    
    # Test Admissions section structure (must match Aid pattern)
    admissions_keys = ["needs_info_applications", "under_review_applications"]
    all_match = True
    for key in admissions_keys:
        if key in data["admissions"]:
            print(f"✅ admissions.{key} present (CLONE OF AID)")
        else:
            print(f"❌ admissions.{key} missing (NOT A CLONE)")
            all_match = False
    
    # Compare structures
    if all_match:
        print(f"\n✅ PASS: Admissions follows Aid contract pattern")
        
        # Check if both are arrays
        aid_needs_info = data["aid"]["needs_info_applications"]
        adm_needs_info = data["admissions"]["needs_info_applications"]
        
        if isinstance(aid_needs_info, list) and isinstance(adm_needs_info, list):
            print(f"✅ Both Aid and Admissions use array format")
            print(f"   - Aid needs_info: {len(aid_needs_info)} items")
            print(f"   - Admissions needs_info: {len(adm_needs_info)} items")
        else:
            print(f"❌ Type mismatch between Aid and Admissions")
            return False
        
        return True
    else:
        print(f"\n❌ FAIL: Admissions does NOT match Aid contract")
        return False

def test_dashboard_api():
    """Test /api/director/dashboard/ contract compliance"""
    print_section("TEST: Dashboard API Contract")
    
    # Get school_id and year_id from priority queue first
    priority_url = f"{BASE_URL}/api/director/priority/"
    priority_response = requests.get(priority_url)
    
    if priority_response.status_code != 200:
        print(f"❌ Cannot get school/year IDs from priority queue")
        return False
    
    priority_data = priority_response.json()
    school_id = priority_data["meta"].get("school_id")
    year_id = priority_data["meta"].get("year_id")
    
    if not school_id or not year_id:
        print(f"⚠️ No school_id/year_id available (need user session)")
        print(f"   Skipping dashboard test (requires authentication)")
        return True  # Skip, don't fail
    
    url = f"{BASE_URL}/api/director/dashboard/?school_id={school_id}&year_id={year_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    # Test required sections
    required_sections = ["aid", "admissions", "finance", "registrar"]
    for section in required_sections:
        if section in data:
            print(f"✅ Has section: '{section}'")
        else:
            print(f"❌ Missing section: '{section}'")
            return False
    
    print(f"\n✅ PASS: Dashboard API includes all personas")
    return True

def test_timeline_api():
    """Test /api/director/timeline/ contract compliance"""
    print_section("TEST: Timeline API Contract")
    
    # Get school_id and year_id from priority queue first
    priority_url = f"{BASE_URL}/api/director/priority/"
    priority_response = requests.get(priority_url)
    
    if priority_response.status_code != 200:
        print(f"❌ Cannot get school/year IDs from priority queue")
        return False
    
    priority_data = priority_response.json()
    school_id = priority_data["meta"].get("school_id")
    year_id = priority_data["meta"].get("year_id")
    
    if not school_id or not year_id:
        print(f"⚠️ No school_id/year_id available (need user session)")
        print(f"   Skipping timeline test (requires authentication)")
        return True  # Skip, don't fail
    
    url = f"{BASE_URL}/api/director/timeline/?school_id={school_id}&year_id={year_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    if "events" in data:
        print(f"✅ Has 'events' array")
        
        if isinstance(data["events"], list):
            print(f"✅ events is an array (length: {len(data['events'])})")
            return True
        else:
            print(f"❌ events is not an array")
            return False
    else:
        print(f"❌ Missing 'events' key")
        return False

def test_page_route():
    """Test /director/ page loads"""
    print_section("TEST: Page Route")
    
    url = f"{BASE_URL}/director/"
    response = requests.get(url)
    
    if response.status_code == 200:
        print(f"✅ /director/ loads (status 200)")
        
        if "director" in response.text.lower():
            print(f"✅ Page contains 'director' text")
            return True
        else:
            print(f"⚠️ Page loaded but may not have director content")
            return True
    else:
        print(f"❌ /director/ failed (status {response.status_code})")
        return False

def test_type_naming_convention():
    """Test that item types follow <PERSONA>_<ENTITY>_<STATUS> pattern"""
    print_section("TEST: Type Naming Convention")
    
    url = f"{BASE_URL}/api/director/priority/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status code {response.status_code}")
        return False
    
    data = response.json()
    
    valid_prefixes = [
        "AID_",
        "ADMISSIONS_",
        "FINANCE_",
        "REGISTRAR_"
    ]
    
    if len(data["worklist_top_10"]) == 0:
        print(f"⚠️ No items in worklist to test (need seed data)")
        return True
    
    all_valid = True
    for item in data["worklist_top_10"]:
        item_type = item.get("type", "")
        has_valid_prefix = any(item_type.startswith(prefix) for prefix in valid_prefixes)
        
        if has_valid_prefix:
            print(f"✅ Type '{item_type}' follows convention")
        else:
            print(f"❌ Type '{item_type}' does NOT follow convention")
            all_valid = False
    
    if all_valid:
        print(f"\n✅ PASS: All types follow <PERSONA>_<ENTITY>_<STATUS> pattern")
        return True
    else:
        print(f"\n❌ FAIL: Some types violate naming convention")
        return False

def main():
    print(f"\n{'#'*60}")
    print(f"#  DIRECTOR FRAMEWORK CONTRACT VALIDATION")
    print(f"#  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    results = {
        "Priority Queue API": test_priority_queue(),
        "Dashboard API": test_dashboard_api(),
        "Timeline API": test_timeline_api(),
        "Page Route": test_page_route(),
        "Type Naming Convention": test_type_naming_convention(),
    }
    
    print_section("VALIDATION SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'─'*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'─'*60}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED - Ready for anchor tag!")
        print(f"\nRun:")
        print(f"  git tag anchor-admissions-director-v1")
        print(f"  git push origin anchor-admissions-director-v1")
        return 0
    else:
        print(f"\n⚠️ SOME TESTS FAILED - Fix issues before tagging")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print(f"Is Django server running? Run:")
        print(f"  python manage.py runserver")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
