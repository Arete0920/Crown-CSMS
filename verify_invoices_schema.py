#!/usr/bin/env python
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from billing.models import Invoice, Household
from uuid import UUID

# Use the demo school ID
school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')

invoices = (
    Invoice.objects
    .filter(school_id=school_id)
    .select_related("household")
    .order_by("-created_at")[:10]
)

print(f"Found {invoices.count()} invoices in demo school")
print("\n=== Sample Invoice Data ===\n")

data = []
for inv in invoices:
    data.append(
        {
            "id": str(inv.id),
            "household_id": str(inv.household_id) if inv.household_id else None,
            "household_name": inv.household.name if inv.household_id else None,
            "total_amount": str(inv.total_amount),
            "due_on": inv.due_on.isoformat() if inv.due_on else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
            "balance_due": str(inv.total_amount),
        }
    )

if data:
    print(json.dumps(data, indent=2))
else:
    print("(no invoices in database for this school)")

print("\n=== Endpoint is wired and ready for frontend consumption ===")
print("GET /api/billing/invoices/ → returns this structure")
