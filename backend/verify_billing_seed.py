import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from billing.models import Invoice, InvoiceLine
from uuid import UUID

school_id = UUID('b45b8c5a-6708-4597-aad9-a226627b2962')

invoices = Invoice.objects.filter(school_id=school_id).select_related('household')
print(f"\n✅ Total invoices: {invoices.count()}")

if invoices.exists():
    sample = invoices.first()
    print(f"\nSample invoice:")
    print(f"  ID: {sample.id}")
    print(f"  Household: {sample.household.name}")
    print(f"  Total: ${sample.total_amount}")
    print(f"  Due: {sample.due_on}")
    
    lines = InvoiceLine.objects.filter(invoice=sample)
    print(f"  Line items: {lines.count()}")
    for line in lines[:3]:
        print(f"    - {line.description}: ${line.amount}")
    
    print(f"\n✅ Finance UI at /finance/invoices will show {invoices.count()} rows")
