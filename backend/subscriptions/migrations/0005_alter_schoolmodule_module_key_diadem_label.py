from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0004_alter_schoolmodule_module_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schoolmodule",
            name="module_key",
            field=models.CharField(
                choices=[
                    ("financial_aid", "Financial Aid Processing"),
                    ("chapel_tracking", "Chapel & Devotional Tracking"),
                    ("gradebook_pro", "Advanced Gradebook"),
                    ("curriculum_mgmt", "Curriculum Management"),
                    ("parent_portal_plus", "Enhanced Parent Portal"),
                    ("home_academy", "Home Academy / Homeschool Affiliation"),
                    ("hr_staff", "HR & Staff Management"),
                    ("little_lambs", "Diadem Daycare Solutions"),
                    ("transportation", "Transportation & Bus Routing"),
                    ("health_office", "Health Office & Nurse Records"),
                    ("alumni", "Alumni Tracking"),
                ],
                db_index=True,
                max_length=50,
            ),
        ),
    ]
