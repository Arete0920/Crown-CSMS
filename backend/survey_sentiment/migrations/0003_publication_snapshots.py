import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("survey_sentiment", "0002_seed_survey_permissions")]

    operations = [
        migrations.CreateModel(
            name="SurveyPublication",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)),
                ("version", models.PositiveIntegerField()),
                ("snapshot_json", models.JSONField(default=dict)),
                ("snapshot_sha256", models.CharField(max_length=64)),
                ("respondent_notice", models.TextField()),
                ("collection_mode", models.CharField(max_length=20, default="anonymous")),
                ("published_by_user_id", models.UUIDField()),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                ("survey", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="publications", to="survey_sentiment.surveydefinition")),
            ],
            options={"ordering": ["version"]},
        ),
        migrations.AddConstraint(
            model_name="surveypublication",
            constraint=models.UniqueConstraint(fields=("survey", "version"), name="survey_pub_unique_version"),
        ),
    ]
