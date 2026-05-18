#!/usr/bin/env python3
"""Compatibility guard for deprecated direct real-ingestion entrypoint.

Canonical dry-run/blocker entrypoint:
    c1_dry_run_ingestion_executor.py
"""

from __future__ import annotations

import sys


def main() -> None:
    print("Use c1_dry_run_ingestion_executor.py")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
