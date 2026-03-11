import os
import sys
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from billing.models import Invoice, InvoiceLine
from uuid import UUID


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

school_id = UUID('b45b8c5a-6708-4597-aad9-a226627b2962')

invoices = Invoice.objects.filter(school_id=school_id).select_related('household')
logger.info("\nTotal invoices: %s", invoices.count())

if invoices.exists():
    sample = invoices.first()
    logger.info("\nSample invoice:")
    logger.info("  ID: %s", sample.id)
    logger.info("  Household: %s", sample.household.name)
    logger.info("  Total: $%s", sample.total_amount)
    logger.info("  Due: %s", sample.due_on)

    lines = InvoiceLine.objects.filter(invoice=sample)
    logger.info("  Line items: %s", lines.count())
    for line in lines[:3]:
        logger.info("    - %s: $%s", line.description, line.amount)

    logger.info("\nFinance UI at /finance/invoices will show %s rows", invoices.count())
