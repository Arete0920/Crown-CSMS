from finance.models import ChartAccount
from core.models import School
import logging


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger.info("ChartAccounts currently in DB:")
for ca in ChartAccount.objects.order_by("id"):
    logger.info("  ID=%s, Code=%s, Name=%s", ca.id, ca.code, ca.name)

if not ChartAccount.objects.exists():
    school = School.objects.first()
    if not school:
        school = School.objects.create(name="Default School", timezone="America/New_York")
        logger.info("Created school: %s", school.name)

    accounts = [
        ("TUITION", "Tuition Revenue", "INCOME"),
        ("AID", "Financial Aid", "EXPENSE"),
        ("FEES", "Fees & Other Income", "INCOME"),
        ("PAYMENT", "Student Payments", "ASSET"),
    ]

    for code, name, atype in accounts:
        ca = ChartAccount.objects.create(
            school=school, code=code, name=name, account_type=atype, is_active=True
        )
        logger.info("Created %s with ID=%s", code, ca.id)
