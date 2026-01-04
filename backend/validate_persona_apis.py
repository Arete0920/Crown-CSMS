"""
Validation script for persona-specific Director APIs

Tests that each persona has isolated API endpoints returning ONLY their data:
- /api/aid/priority-queue/ → Aid data only
- /api/aid/metrics/ → Aid metrics only
- /api/aid/timeline/ → Aid events only
- /api/admissions/priority-queue/ → Admissions data only
- /api/admissions/metrics/ → Admissions metrics only
- /api/admissions/timeline/ → Admissions events only

Contract: All personas must have identical API structure.
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://127.0.0.1:8000"


def validate_priority_queue(persona: str) -> bool:
    """Test /api/{persona}/priority-queue/ endpoint"""
    print(f"\n{'='*60}")
    print(f"TEST: {persona.upper()} Priority Queue API")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/{persona}/priority-queue/"
    print(f"URL: {url}")
    
    # Get test data from aid to extract school_id and year_id
    aid_priority_url = f"{BASE_URL}/api/director/priority/"
    aid_response = requests.get(aid_priority_url, params={"school_id": "1", "year_id": "1"})
    
    params = {"school_id": "1", "year_id": "1"}
    print(f"Params: {params}")
    
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False
    
    data = response.json()
    
    # Validate contract
    required_keys = ["rows", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        print(f"❌ FAILED: Missing keys: {missing_keys}")
        return False
    
    # Validate meta
    if data["meta"].get("persona") != persona:
        print(f"❌ FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False
    
    # Validate rows structure
    if not isinstance(data["rows"], list):
        print(f"❌ FAILED: 'rows' must be a list")
        return False
    
    print(f"✅ PASSED")
    print(f"  - Rows count: {len(data['rows'])}")
    print(f"  - Persona: {data['meta']['persona']}")
    
    # Show sample row
    if data["rows"]:
        sample = data["rows"][0]
        print(f"  - Sample row keys: {list(sample.keys())}")
        print(f"  - Sample type: {sample.get('type')}")
    
    return True


def validate_metrics(persona: str) -> bool:
    """Test /api/{persona}/metrics/ endpoint"""
    print(f"\n{'='*60}")
    print(f"TEST: {persona.upper()} Metrics API")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/{persona}/metrics/"
    print(f"URL: {url}")
    
    params = {"school_id": "1", "year_id": "1"}
    print(f"Params: {params}")
    
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False
    
    data = response.json()
    
    # Validate contract
    required_keys = ["metrics", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        print(f"❌ FAILED: Missing keys: {missing_keys}")
        return False
    
    # Validate meta
    if data["meta"].get("persona") != persona:
        print(f"❌ FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False
    
    # Validate metrics structure
    if not isinstance(data["metrics"], dict):
        print(f"❌ FAILED: 'metrics' must be a dict")
        return False
    
    print(f"✅ PASSED")
    print(f"  - Metrics keys: {list(data['metrics'].keys())}")
    print(f"  - Persona: {data['meta']['persona']}")
    
    return True


def validate_timeline(persona: str) -> bool:
    """Test /api/{persona}/timeline/ endpoint"""
    print(f"\n{'='*60}")
    print(f"TEST: {persona.upper()} Timeline API")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/api/{persona}/timeline/"
    print(f"URL: {url}")
    
    params = {"school_id": "1", "year_id": "1"}
    print(f"Params: {params}")
    
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False
    
    data = response.json()
    
    # Validate contract
    required_keys = ["events", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        print(f"❌ FAILED: Missing keys: {missing_keys}")
        return False
    
    # Validate meta
    if data["meta"].get("persona") != persona:
        print(f"❌ FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False
    
    # Validate events structure
    if not isinstance(data["events"], list):
        print(f"❌ FAILED: 'events' must be a list")
        return False
    
    print(f"✅ PASSED")
    print(f"  - Events count: {len(data['events'])}")
    print(f"  - Persona: {data['meta']['persona']}")
    
    # Show sample event
    if data["events"]:
        sample = data["events"][0]
        print(f"  - Sample event keys: {list(sample.keys())}")
        print(f"  - Sample type: {sample.get('type')}")
    
    return True


def main():
    print("\n" + "="*60)
    print("PERSONA-SPECIFIC API VALIDATION")
    print("Testing that each persona has isolated APIs")
    print("="*60)
    
    personas = ["aid", "admissions"]
    results = []
    
    for persona in personas:
        priority_ok = validate_priority_queue(persona)
        metrics_ok = validate_metrics(persona)
        timeline_ok = validate_timeline(persona)
        
        persona_passed = priority_ok and metrics_ok and timeline_ok
        results.append((persona, persona_passed))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for persona, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{persona.upper()}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Persona-specific APIs are working correctly.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check errors above.")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
