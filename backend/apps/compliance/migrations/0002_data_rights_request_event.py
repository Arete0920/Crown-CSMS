from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("compliance", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="consentaudit",
            name="consent_type",
            field=models.CharField(
                choices=[
                    ("privacy_policy", "Privacy Policy"),
                    ("school_authorization", "School Authorization"),
                    ("parental_consent", "Parental Consent"),
                    ("data_rights_request", "Data Rights Request (Not Consent)"),
                    ("faith_data_acknowledgement", "Faith Data Acknowledgement"),
                ],
                max_length=64,
            ),
        ),
    ]
