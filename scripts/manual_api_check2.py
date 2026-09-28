import os
import requests

# Get households without auth (should fail with 401)
response1 = requests.get("https://crown2026-api-dev.azurewebsites.net/api/households/")
print(f"Households (no auth): {response1.status_code}")

# Get health
response2 = requests.get("https://crown2026-api-dev.azurewebsites.net/health/")
print(f"Health: {response2.status_code} - {response2.json()}")

# Try to get JWT token
try:
    token_response = requests.post(
        "https://crown2026-api-dev.azurewebsites.net/api/auth/token/",
        json={"username": "admin", "password": os.environ["DEV_ADMIN_PASSWORD"]},
        timeout=10
    )
    print(f"\nToken endpoint: {token_response.status_code}")
    if token_response.status_code == 200:
        print("✓ Token obtained successfully")
        token = token_response.json()['access']

        # Try households with auth
        hh_response = requests.get(
            "https://crown2026-api-dev.azurewebsites.net/api/households/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"Households (with auth): {hh_response.status_code}")
        data = hh_response.json()
        print(f"Data: {data}")
    else:
        print(f"✗ Token failed: {token_response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
