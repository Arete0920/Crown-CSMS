"""
Director Framework Contract Validation Script

Tests that Admissions Director follows the same contract as Aid Director (gold standard).
"""

import logging
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:8000"
logger = logging.getLogger(__name__)


def _out(message: str) -> None:
    logger.info("%s", message)


def print_section(title: str) -> None:
    _out(f"\n{'=' * 60}")
    _out(f"  {title}")
    _out(f"{'=' * 60}\n")


def test_priority_queue() -> bool:
    """Test /api/director/priority/ contract compliance"""
    print_section("TEST: Priority Queue API Contract")

    url = f"{BASE_URL}/api/director/priority/"
    response = requests.get(url)

    if response.status_code != 200:
        _out(f"FAILED: Status code {response.status_code}")
        return False

    data = response.json()

    required_keys = ["meta", "worklist_top_10", "aid", "admissions", "finance", "registrar"]
    for key in required_keys:
        if key in data:
            _out(f"OK Has required key: '{key}'")
        else:
            _out(f"FAILED Missing required key: '{key}'")
            return False

    for key in ["school_id", "year_id"]:
        if key in data["meta"]:
            _out(f"OK meta.{key} present")
        else:
            _out(f"FAILED meta.{key} missing")
            return False

    if isinstance(data["worklist_top_10"], list):
        _out(f"OK worklist_top_10 is array (length: {len(data['worklist_top_10'])})")
        if data["worklist_top_10"]:
            item = data["worklist_top_10"][0]
            for key in ["type", "score", "id", "summary"]:
                if key in item:
                    _out(f"OK worklist item has '{key}'")
                else:
                    _out(f"FAILED worklist item missing '{key}'")
    else:
        _out("FAILED worklist_top_10 is not an array")
        return False

    for key in ["needs_info_applications", "under_review_applications", "accepted_not_posted_awards"]:
        if key in data["aid"]:
            _out(f"OK aid.{key} present")
        else:
            _out(f"FAILED aid.{key} missing")

    all_match = True
    for key in ["needs_info_applications", "under_review_applications"]:
        if key in data["admissions"]:
            _out(f"OK admissions.{key} present (CLONE OF AID)")
        else:
            _out(f"FAILED admissions.{key} missing (NOT A CLONE)")
            all_match = False

    if all_match:
        _out("\nPASS: Admissions follows Aid contract pattern")
        aid_needs_info = data["aid"]["needs_info_applications"]
        adm_needs_info = data["admissions"]["needs_info_applications"]
        if isinstance(aid_needs_info, list) and isinstance(adm_needs_info, list):
            _out("OK Both Aid and Admissions use array format")
            _out(f"   - Aid needs_info: {len(aid_needs_info)} items")
            _out(f"   - Admissions needs_info: {len(adm_needs_info)} items")
            return True
        _out("FAILED Type mismatch between Aid and Admissions")
        return False

    _out("\nFAIL: Admissions does NOT match Aid contract")
    return False


def test_dashboard_api() -> bool:
    print_section("TEST: Dashboard API Contract")

    priority_url = f"{BASE_URL}/api/director/priority/"
    priority_response = requests.get(priority_url)

    if priority_response.status_code != 200:
        _out("FAILED Cannot get school/year IDs from priority queue")
        return False

    priority_data = priority_response.json()
    school_id = priority_data["meta"].get("school_id")
    year_id = priority_data["meta"].get("year_id")

    if not school_id or not year_id:
        _out("WARN No school_id/year_id available (need user session)")
        _out("   Skipping dashboard test (requires authentication)")
        return True

    response = requests.get(f"{BASE_URL}/api/director/dashboard/?school_id={school_id}&year_id={year_id}")
    if response.status_code != 200:
        _out(f"FAILED: Status code {response.status_code}")
        return False

    data = response.json()
    for section in ["aid", "admissions", "finance", "registrar"]:
        if section in data:
            _out(f"OK Has section: '{section}'")
        else:
            _out(f"FAILED Missing section: '{section}'")
            return False

    _out("\nPASS: Dashboard API includes all personas")
    return True


def test_timeline_api() -> bool:
    print_section("TEST: Timeline API Contract")

    priority_response = requests.get(f"{BASE_URL}/api/director/priority/")
    if priority_response.status_code != 200:
        _out("FAILED Cannot get school/year IDs from priority queue")
        return False

    priority_data = priority_response.json()
    school_id = priority_data["meta"].get("school_id")
    year_id = priority_data["meta"].get("year_id")

    if not school_id or not year_id:
        _out("WARN No school_id/year_id available (need user session)")
        _out("   Skipping timeline test (requires authentication)")
        return True

    response = requests.get(f"{BASE_URL}/api/director/timeline/?school_id={school_id}&year_id={year_id}")
    if response.status_code != 200:
        _out(f"FAILED: Status code {response.status_code}")
        return False

    data = response.json()
    if "events" not in data:
        _out("FAILED Missing 'events' key")
        return False
    if not isinstance(data["events"], list):
        _out("FAILED events is not an array")
        return False

    _out("OK Has 'events' array")
    _out(f"OK events is an array (length: {len(data['events'])})")
    return True


def test_page_route() -> bool:
    print_section("TEST: Page Route")

    response = requests.get(f"{BASE_URL}/director/")
    if response.status_code == 200:
        _out("OK /director/ loads (status 200)")
        if "director" in response.text.lower():
            _out("OK Page contains 'director' text")
        else:
            _out("WARN Page loaded but may not have director content")
        return True

    _out(f"FAILED /director/ failed (status {response.status_code})")
    return False


def test_type_naming_convention() -> bool:
    print_section("TEST: Type Naming Convention")

    response = requests.get(f"{BASE_URL}/api/director/priority/")
    if response.status_code != 200:
        _out(f"FAILED: Status code {response.status_code}")
        return False

    data = response.json()
    valid_prefixes = ["AID_", "ADMISSIONS_", "FINANCE_", "REGISTRAR_"]

    if len(data["worklist_top_10"]) == 0:
        _out("WARN No items in worklist to test (need seed data)")
        return True

    all_valid = True
    for item in data["worklist_top_10"]:
        item_type = item.get("type", "")
        if any(item_type.startswith(prefix) for prefix in valid_prefixes):
            _out(f"OK Type '{item_type}' follows convention")
        else:
            _out(f"FAILED Type '{item_type}' does NOT follow convention")
            all_valid = False

    if all_valid:
        _out("\nPASS: All types follow <PERSONA>_<ENTITY>_<STATUS> pattern")
    else:
        _out("\nFAIL: Some types violate naming convention")
    return all_valid


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    _out(f"\n{'#' * 60}")
    _out("#  DIRECTOR FRAMEWORK CONTRACT VALIDATION")
    _out(f"#  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _out(f"{'#' * 60}")

    results = {
        "Priority Queue API": test_priority_queue(),
        "Dashboard API": test_dashboard_api(),
        "Timeline API": test_timeline_api(),
        "Page Route": test_page_route(),
        "Type Naming Convention": test_type_naming_convention(),
    }

    print_section("VALIDATION SUMMARY")
    total = len(results)
    passed = sum(1 for ok in results.values() if ok)

    for test_name, passed_test in results.items():
        status = "PASS" if passed_test else "FAIL"
        _out(f"{status} - {test_name}")

    _out(f"\n{'-' * 60}")
    _out(f"Results: {passed}/{total} tests passed")
    _out(f"{'-' * 60}")

    if passed == total:
        _out("\nALL TESTS PASSED - Ready for anchor tag!")
        _out("\nRun:")
        _out("  git tag anchor-admissions-director-v1")
        _out("  git push origin anchor-admissions-director-v1")
        return 0

    _out("\nSOME TESTS FAILED - Fix issues before tagging")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.exceptions.ConnectionError:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        _out(f"\nERROR: Cannot connect to {BASE_URL}")
        _out("Is Django server running? Run:")
        _out("  python manage.py runserver")
        raise SystemExit(1)
    except Exception as e:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        _out(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
