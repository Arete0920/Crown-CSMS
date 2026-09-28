import os
import requests
import json

# Get JWT token
response = requests.post(
    "https://crown2026-api-dev.azurewebsites.net/api/auth/token/",
    json={"username": "admin", "password": os.environ["DEV_ADMIN_PASSWORD"]}
)
print(f"Token response status: {response.status_code}")


if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access']
    print("Access token obtained successfully")

    # Test households endpoint
    households_response = requests.get(
        "https://crown2026-api-dev.azurewebsites.net/api/households/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"\nHouseholds response status: {households_response.status_code}")
    households_data = households_response.json()
    print(f"Number of households: {len(households_data)}")
    if len(households_data) > 0:
        print(f"\nFirst 3 households:")
        for hh in households_data[:3]:
            print(f"  - ID: {hh.get('id')}, Name: {hh.get('household_name')}")
    else:
        print("No households found - bootstrap may not have run successfully")
