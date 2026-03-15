import os, django, sys
import logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from finance.models import ChartAccount
from core.models import School


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Show existing
existing = list(ChartAccount.objects.order_by("id"))
if existing:
    logger.info("\n=== Existing ChartAccounts ===")
    for ca in existing:
        logger.info("ID: %s, Code: %s", ca.id, ca.code)
    sys.exit(0)

logger.info("\n=== Creating foundational ChartAccounts ===")
school = School.objects.first() or School.objects.create(name="Default School", timezone="America/New_York")

for code, name, atype in [("TUITION", "Tuition Revenue", "INCOME"), ("AID", "Financial Aid", "EXPENSE"), ("FEES", "Fees", "INCOME"), ("PAYMENT", "Payments", "ASSET")]:
    ca = ChartAccount.objects.create(school=school, code=code, name=name, account_type=atype)
    logger.info("Created %s: ID=%s", code, ca.id)

logger.info("\n=== All ChartAccounts ===")
for ca in ChartAccount.objects.order_by("id"):
    logger.info("ID: %s, Code: %s", ca.id, ca.code)
