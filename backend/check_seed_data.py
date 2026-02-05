import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from households.models import Household
from core.models import School

print(f"Schools: {School.objects.count()}")
print(f"Households: {Household.objects.count()}")

if Household.objects.exists():
    h = Household.objects.first()
    print(f"Sample household school_id: {h.school_id}")
    print(f"Students in first household: {h.students.count()}")
else:
    if School.objects.exists():
        s = School.objects.first()
        print(f"First school ID: {s.id}")
