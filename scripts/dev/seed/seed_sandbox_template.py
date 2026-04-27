"""
CROWN sandbox seed template.

Public-safe example only.
Do not hardcode school IDs, tenant IDs, real people, credentials, or production data.
Convert this into a Django management command before production use.
"""

import os

SCHOOL_ID = os.getenv("CROWN_SANDBOX_SCHOOL_ID")
DJANGO_SETTINGS_MODULE = os.getenv("DJANGO_SETTINGS_MODULE", "crown2026_config.settings")


def main() -> int:
    if not SCHOOL_ID:
        print("Missing CROWN_SANDBOX_SCHOOL_ID. Refusing to seed without explicit sandbox school context.")
        return 2

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

    print("Public-safe seed template.")
    print(f"Settings module: {DJANGO_SETTINGS_MODULE}")
    print(f"Sandbox school ID provided: {SCHOOL_ID[:8]}...")
    print("Add tenant-scoped sandbox seed logic here or convert to a Django management command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
