"""
D3 Production Gate Sweep - API Smoke Tests
Tests new endpoints with authentication
"""
import requests
import sys
import json

BASE_URL = "http://127.0.0.1:8000"
SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962"

def get_auth_token():
    """Login and get authentication token."""
    try:
        with open('login.json', 'r') as f:
            creds = json.load(f)
        response = requests.post(
            f"{BASE_URL}/api/auth/token/",
            json=creds,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('access')  # JWT returns 'access' token
        else:
            print(f"⚠️  Login failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"⚠️  Login error: {e}")
        return None

def test_endpoint(name, url, token=None, expected_status=200):
    """Test endpoint and report result"""
    try:
        headers = {"X-School-ID": SCHOOL_ID}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(url, headers=headers, timeout=5)
        status_ok = response.status_code == expected_status
        
        result = "✅" if status_ok else "❌"
        print(f"{result} {name}: {response.status_code}")
        
        if status_ok and response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"   → Returned {len(data)} items")
                elif isinstance(data, dict):
                    print(f"   → Returned dict with {len(data)} keys")
            except:
                pass
        
        return status_ok
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Server not responding")
        return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("D3 Production Gate Sweep - API Smoke Tests")
    print("=" * 60)
    print()
    
    # Get authentication token
    print("🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token - cannot proceed")
        return 1
    print("✅ Authentication successful")
    print()
    
    tests = [
        ("Health Check", f"{BASE_URL}/", None),  # No auth needed
        ("Billing Invoices (NEW)", f"{BASE_URL}/api/billing/invoices/", token),
        ("Threads List (NEW)", f"{BASE_URL}/api/threads/", token),
        ("Admissions Applications", f"{BASE_URL}/api/admissions/applications/", token),
        ("Gradebook Sections", f"{BASE_URL}/api/gradebook/sections/", token),
    ]
    
    results = []
    for name, url, auth_token in tests:
        results.append(test_endpoint(name, url, token=auth_token))
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All API smoke tests passed")
        return 0
    else:
        print("⚠️  Some tests failed - review output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
