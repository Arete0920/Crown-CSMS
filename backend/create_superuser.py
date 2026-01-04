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
print(f"✓ Superuser created: {user.username}")
print(f"  Username: admin")
print(f"  Password: Crown2026!")
