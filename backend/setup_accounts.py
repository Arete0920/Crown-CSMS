import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from finance.models import ChartAccount
from core.models import School

# Show existing
existing = list(ChartAccount.objects.all())
if existing:
    print("\n=== Existing ChartAccounts ===")
    for ca in existing:
        print(f"ID: {ca.id}, Code: {ca.code}")
    sys.exit(0)

print("\n=== Creating foundational ChartAccounts ===")
school = School.objects.first() or School.objects.create(name="Default School", timezone="America/New_York")

for code, name, atype in [("TUITION", "Tuition Revenue", "INCOME"), ("AID", "Financial Aid", "EXPENSE"), ("FEES", "Fees", "INCOME"), ("PAYMENT", "Payments", "ASSET")]:
    ca = ChartAccount.objects.create(school=school, code=code, name=name, account_type=atype)
    print(f"✓ Created {code}: ID={ca.id}")

print("\n=== All ChartAccounts ===")
for ca in ChartAccount.objects.all():
    print(f"ID: {ca.id}, Code: {ca.code}")
