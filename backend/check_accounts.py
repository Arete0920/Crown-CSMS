from finance.models import ChartAccount
from core.models import School

print("ChartAccounts currently in DB:")
for ca in ChartAccount.objects.all():
    print(f"  ID={ca.id}, Code={ca.code}, Name={ca.name}")

if not ChartAccount.objects.exists():
    school = School.objects.first()
    if not school:
        school = School.objects.create(name="Default School", timezone="America/New_York")
        print(f"Created school: {school.name}")
    
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
        print(f"✓ Created {code} with ID={ca.id}")
