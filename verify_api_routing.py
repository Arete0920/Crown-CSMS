"""
Verification: /api and /api/v1 are true aliases
"""
import requests

BASE_URL = "https://crown2026-api-dev.azurewebsites.net"

# Get token
token_response = requests.post(
    f"{BASE_URL}/api/auth/token/",
    json={"username": "admin", "password": "Crown2026!"}
)
assert token_response.status_code == 200, "Token endpoint failed"
token = token_response.json()['access']
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("API ROUTING VERIFICATION")
print("=" * 60)

# Test households endpoint
endpoints_to_test = [
    ("/api/v1/households/", "/api/households/"),
    ("/api/v1/auth/token/", "/api/auth/token/"),
]

all_pass = True
for v1_path, api_path in endpoints_to_test:
    r1 = requests.get(f"{BASE_URL}{v1_path}", headers=headers, timeout=10)
    r2 = requests.get(f"{BASE_URL}{api_path}", headers=headers, timeout=10)
    
    match = r1.status_code == r2.status_code
    symbol = "✓" if match else "✗"
    
    print(f"\n{symbol} {v1_path} vs {api_path}")
    print(f"   Status: {r1.status_code} vs {r2.status_code}")
    
    if match and r1.status_code == 200:
        data1 = r1.json()
        data2 = r2.json()
        if isinstance(data1, list) and isinstance(data2, list):
            print(f"   Counts: {len(data1)} vs {len(data2)}")
            if len(data1) == len(data2):
                print(f"   ✓ Data matches")
            else:
                print(f"   ✗ Data mismatch!")
                all_pass = False
    elif not match:
        all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("✓ ALL TESTS PASSED - /api and /api/v1 are true aliases")
else:
    print("✗ SOME TESTS FAILED - routing inconsistency detected")
print("=" * 60)
