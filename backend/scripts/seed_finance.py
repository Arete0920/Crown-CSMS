"""Deterministic local seed for Finance module (Invoice + Payment).

Safe-by-default:
- Refuses to run on Azure (WEBSITE_HOSTNAME/WEBSITE_INSTANCE_ID present)
- Uses get_or_create so it can be re-run without duplicating

Usage (PowerShell):
  cd backend
    .\\venv\\Scripts\\python.exe ..\\backend\\scripts\\seed_finance.py

Note: This seed expects households from scripts/seed_households.py.
"""

import os
import re
from datetime import date


def _refuse_if_azure() -> None:
  if os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"):
    raise SystemExit("Refusing to run seed_finance on Azure/production.")


def _short_slug(name: str) -> str:
  slug = re.sub(r"[^A-Za-z0-9]+", "", (name or "").upper())
  return slug[:6] or "HOUSE"


def run() -> None:
  _refuse_if_azure()

  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

  import django

  django.setup()

  from crown_api.models import Household, Invoice, Payment

  households = list(Household.objects.all().order_by("household_name"))
  if not households:
    raise SystemExit("No households found. Run scripts/seed_households.py first.")

  for household in households:
    short = _short_slug(household.household_name)

    Invoice.objects.get_or_create(
      household=household,
      invoice_number=f"INV-{short}-0001",
      defaults={
        "amount_cents": 150000,
        "status": Invoice.STATUS_OPEN,
        "issued_date": date(2026, 1, 1),
        "due_date": date(2026, 2, 1),
      },
    )
    Invoice.objects.get_or_create(
      household=household,
      invoice_number=f"INV-{short}-0002",
      defaults={
        "amount_cents": 150000,
        "status": Invoice.STATUS_PAID,
        "issued_date": date(2025, 12, 1),
        "due_date": date(2026, 1, 1),
      },
    )

    Payment.objects.get_or_create(
      household=household,
      payment_reference=f"PAY-{short}-0001",
      defaults={
        "amount_cents": 150000,
        "payment_date": date(2026, 1, 15),
      },
    )

  print("Seeded finance:")
  print(f"- Invoices: {Invoice.objects.count()}")
  print(f"- Payments: {Payment.objects.count()}")


if __name__ == "__main__":
  run()
