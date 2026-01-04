"""
Test script to verify admissions was properly added to director_priority API
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from crown_api.director_views import director_priority
from django.test import RequestFactory
from core.models import UserAccount, School, AcademicYear
from admissions.models import AdmissionsApplication
from aid.models import AidApplication

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/director/priority/')

# Create a test user (or get existing one)
try:
    user = UserAccount.objects.first()
    if not user:
        print("❌ No users found in database. Run populate.py first.")
        exit(1)
    
    request.user = user
    
    # Get school and year
    school = School.objects.first()
    academic_year = AcademicYear.objects.filter(school=school).first()
    
    if not school or not academic_year:
        print("❌ No school/academic year found. Run populate.py first.")
        exit(1)
    
    print(f"✅ Testing with user: {user.email}")
    print(f"✅ School: {school.name}")
    print(f"✅ Academic Year: {academic_year.name}")
    
    # Count applications
    aid_count = AidApplication.objects.filter(
        school=school, 
        academic_year=academic_year
    ).count()
    admissions_count = AdmissionsApplication.objects.filter(
        school=school,
        academic_year=academic_year
    ).count()
    
    print(f"\n📊 Database counts:")
    print(f"   Aid applications: {aid_count}")
    print(f"   Admissions applications: {admissions_count}")
    
    # Call the API function
    print(f"\n🔍 Calling director_priority()...")
    response = director_priority(request)
    
    if response.status_code == 200:
        data = response.data
        print(f"✅ API call successful!")
        print(f"\n📈 Response structure:")
        print(f"   - worklist_top_10: {len(data.get('worklist_top_10', []))} items")
        
        # Show worklist item types
        if 'worklist_top_10' in data:
            types = {}
            for item in data['worklist_top_10']:
                item_type = item.get('type', 'UNKNOWN')
                types[item_type] = types.get(item_type, 0) + 1
            
            print(f"\n   Worklist breakdown by type:")
            for item_type, count in sorted(types.items()):
                print(f"      - {item_type}: {count}")
        
        # Check for admissions sections
        if 'admissions' in data:
            adm = data['admissions']
            print(f"\n   - admissions.needs_info_applications: {len(adm.get('needs_info_applications', []))}")
            print(f"   - admissions.under_review_applications: {len(adm.get('under_review_applications', []))}")
            print(f"\n✅ Admissions section present in response!")
        else:
            print(f"\n❌ Admissions section missing from response!")
        
        if 'aid' in data:
            aid = data['aid']
            print(f"\n   - aid.needs_info_applications: {len(aid.get('needs_info_applications', []))}")
            print(f"   - aid.under_review_applications: {len(aid.get('under_review_applications', []))}")
    else:
        print(f"❌ API call failed with status {response.status_code}")
        print(f"Response: {response.data}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
