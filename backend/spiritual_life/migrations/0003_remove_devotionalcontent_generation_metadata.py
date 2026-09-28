from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("spiritual_life", "0002_alter_prayerrequest_visibility_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="devotionalcontent",
            name="generated_by_ai",
        ),
    ]
