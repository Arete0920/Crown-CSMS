from django.contrib.auth import get_user_model

User = get_user_model()

# Delete existing admin if exists
User.objects.filter(username='admin').delete()

# Create new superuser
user = User.objects.create_superuser(
    username='admin',
    email='admin@crown.local',
    password='Crown2026!'
)

# Attach a school context for tenant-scoped APIs (exports/billing/etc.).
# Many local flows use a superuser without a School assigned, which will 403.
try:
    from core.models import School

    school = School.objects.first()
    if school is not None and hasattr(user, "school_id"):
        user.school = school
        user.save(update_fields=["school"])
        print(f"  School: {school.id} ({school.name})")
except Exception:
    # If core.School isn't available in this deployment, skip silently.
    pass

print(f"✓ Superuser created: {user.username}")
print(f"  Username: admin")
print(f"  Password: Crown2026!")
