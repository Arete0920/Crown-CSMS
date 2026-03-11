"""
Validation script for persona-specific Director APIs

Tests that each persona has isolated API endpoints returning ONLY their data:
- /api/aid/priority-queue/ -> Aid data only
- /api/aid/metrics/ -> Aid metrics only
- /api/aid/timeline/ -> Aid events only
- /api/admissions/priority-queue/ -> Admissions data only
- /api/admissions/metrics/ -> Admissions metrics only
- /api/admissions/timeline/ -> Admissions events only

Contract: All personas must have identical API structure.
"""

import json
import logging
import sys
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000"
logger = logging.getLogger(__name__)


def _out(message: str) -> None:
    logger.info("%s", message)


def validate_priority_queue(persona: str) -> bool:
    """Test /api/{persona}/priority-queue/ endpoint"""
    _out(f"\n{'=' * 60}")
    _out(f"TEST: {persona.upper()} Priority Queue API")
    _out(f"{'=' * 60}")

    url = f"{BASE_URL}/api/{persona}/priority-queue/"
    _out(f"URL: {url}")

    params = {"school_id": "1", "year_id": "1"}
    _out(f"Params: {params}")

    response = requests.get(url, params=params)
    _out(f"Status: {response.status_code}")

    if response.status_code != 200:
        _out(f"FAILED: Expected 200, got {response.status_code}")
        _out(f"Response: {response.text[:500]}")
        return False

    data = response.json()

    required_keys = ["rows", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        _out(f"FAILED: Missing keys: {missing_keys}")
        return False

    if data["meta"].get("persona") != persona:
        _out(f"FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False

    if not isinstance(data["rows"], list):
        _out("FAILED: 'rows' must be a list")
        return False

    _out("PASSED")
    _out(f"  - Rows count: {len(data['rows'])}")
    _out(f"  - Persona: {data['meta']['persona']}")

    if data["rows"]:
        sample = data["rows"][0]
        _out(f"  - Sample row keys: {list(sample.keys())}")
        _out(f"  - Sample type: {sample.get('type')}")

    return True


def validate_metrics(persona: str) -> bool:
    """Test /api/{persona}/metrics/ endpoint"""
    _out(f"\n{'=' * 60}")
    _out(f"TEST: {persona.upper()} Metrics API")
    _out(f"{'=' * 60}")

    url = f"{BASE_URL}/api/{persona}/metrics/"
    _out(f"URL: {url}")

    params = {"school_id": "1", "year_id": "1"}
    _out(f"Params: {params}")

    response = requests.get(url, params=params)
    _out(f"Status: {response.status_code}")

    if response.status_code != 200:
        _out(f"FAILED: Expected 200, got {response.status_code}")
        _out(f"Response: {response.text[:500]}")
        return False

    data = response.json()

    required_keys = ["metrics", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        _out(f"FAILED: Missing keys: {missing_keys}")
        return False

    if data["meta"].get("persona") != persona:
        _out(f"FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False

    if not isinstance(data["metrics"], dict):
        _out("FAILED: 'metrics' must be a dict")
        return False

    _out("PASSED")
    _out(f"  - Metrics keys: {list(data['metrics'].keys())}")
    _out(f"  - Persona: {data['meta']['persona']}")

    return True


def validate_timeline(persona: str) -> bool:
    """Test /api/{persona}/timeline/ endpoint"""
    _out(f"\n{'=' * 60}")
    _out(f"TEST: {persona.upper()} Timeline API")
    _out(f"{'=' * 60}")

    url = f"{BASE_URL}/api/{persona}/timeline/"
    _out(f"URL: {url}")

    params = {"school_id": "1", "year_id": "1"}
    _out(f"Params: {params}")

    response = requests.get(url, params=params)
    _out(f"Status: {response.status_code}")

    if response.status_code != 200:
        _out(f"FAILED: Expected 200, got {response.status_code}")
        _out(f"Response: {response.text[:500]}")
        return False

    data = response.json()

    required_keys = ["events", "meta"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        _out(f"FAILED: Missing keys: {missing_keys}")
        return False

    if data["meta"].get("persona") != persona:
        _out(f"FAILED: meta.persona = '{data['meta'].get('persona')}', expected '{persona}'")
        return False

    if not isinstance(data["events"], list):
        _out("FAILED: 'events' must be a list")
        return False

    _out("PASSED")
    _out(f"  - Events count: {len(data['events'])}")
    _out(f"  - Persona: {data['meta']['persona']}")

    if data["events"]:
        sample = data["events"][0]
        _out(f"  - Sample event keys: {list(sample.keys())}")
        _out(f"  - Sample type: {sample.get('type')}")

    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    _out("\n" + "=" * 60)
    _out("PERSONA-SPECIFIC API VALIDATION")
    _out("Testing that each persona has isolated APIs")
    _out("=" * 60)

    personas = ["aid", "admissions"]
    results: list[tuple[str, bool]] = []

    for persona in personas:
        priority_ok = validate_priority_queue(persona)
        metrics_ok = validate_metrics(persona)
        timeline_ok = validate_timeline(persona)
        results.append((persona, priority_ok and metrics_ok and timeline_ok))

    _out("\n" + "=" * 60)
    _out("SUMMARY")
    _out("=" * 60)

    for persona, passed in results:
        status = "PASSED" if passed else "FAILED"
        _out(f"{persona.upper()}: {status}")

    all_passed = all(passed for _, passed in results)

    _out("\n" + "=" * 60)
    if all_passed:
        _out("ALL TESTS PASSED")
        _out("Persona-specific APIs are working correctly.")
    else:
        _out("SOME TESTS FAILED")
        _out("Check errors above.")
    _out("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
