from finance.models import ChartAccount
from core.models import School

# Get or create a school context (we'll use the first school, or create one)
school = School.objects.first()
if not school:
    school = School.objects.create(name="Default School", timezone="America/New_York", is_active=True)
    print(f"Created school: {school.name}")

# Create foundational chart accounts
accounts = [
    ("TUITION", "Tuition Revenue", "INCOME"),
    ("AID", "Financial Aid", "EXPENSE"),
    ("FEES", "Fees & Other Income", "INCOME"),
    ("PAYMENT", "Student Payments", "ASSET"),
]

for code, name, account_type in accounts:
    obj, created = ChartAccount.objects.get_or_create(
        school=school,
        code=code,
        defaults={
            "name": name,
            "account_type": account_type,
            "is_active": True,
        }
    )
    status = "created" if created else "exists"
    print(f"✓ {code} ({status}): ID={obj.id}")
