"""
CROWN manual auth check template.

Public-safe example only.
Do not hardcode emails, passwords, school IDs, bearer tokens, or tenant IDs.
Use environment variables.
"""

import os
import requests

BASE_URL = os.getenv("CROWN_BASE_URL", "http://127.0.0.1:8000")
EMAIL = os.getenv("CROWN_SANDBOX_EMAIL")
PASSWORD = os.getenv("CROWN_SANDBOX_PASSWORD")


def main() -> int:
    if not EMAIL or not PASSWORD:
        print(
            "Missing CROWN_SANDBOX_EMAIL or CROWN_SANDBOX_PASSWORD. "
            "Set them in your local environment. Do not commit credentials."
        )
        return 2

    response = requests.post(
        f"{BASE_URL.rstrip('/')}/api/token/",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=20,
    )

    print(f"Status: {response.status_code}")
    if response.ok:
        payload = response.json()
        safe_keys = sorted(k for k in payload.keys() if k.lower() not in {"access", "refresh", "token"})
        print(f"Authenticated. Response keys excluding tokens: {safe_keys}")
        return 0

    print(response.text[:1000])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
