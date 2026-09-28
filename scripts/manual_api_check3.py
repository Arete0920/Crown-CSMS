import os
import requests

token_response = requests.post(
    "https://crown2026-api-dev.azurewebsites.net/api/auth/token/",
    json={"username": "admin", "password": os.environ["DEV_ADMIN_PASSWORD"]}
)
token = token_response.json()['access']

endpoints = [
    "/api/households/",
    "/api/v1/households/",  # Alternative endpoint
    "/api/core/schools/",
]

for endpoint in endpoints:
    url = f"https://crown2026-api-dev.azurewebsites.net{endpoint}"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"{endpoint}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  Count: {len(data)}")
                if len(data) > 0:
                    print(f"  First item: {data[0]}")
            else:
                print(f"  Data: {data}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {e}")
