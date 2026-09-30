import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("core", "0017_seed_marketing_edit_permission"),
    ]
    operations = [
        migrations.CreateModel(
            name="SurveyDefinition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=180)),
                ("purpose", models.CharField(choices=[("inquiry","Inquiry"),("post_tour","Post Tour"),("new_family","New Family"),("parent_pulse","Parent Pulse"),("reenrollment_intent","Re-enrollment Intent"),("lost_prospect","Lost Prospect"),("exit","Exit"),("custom","Custom")], db_index=True, max_length=32)),
                ("status", models.CharField(choices=[("draft","Draft"),("active","Active"),("closed","Closed"),("archived","Archived")], db_index=True, default="draft", max_length=20)),
                ("anonymous_allowed", models.BooleanField(default=False)),
                ("public_enabled", models.BooleanField(default=False)),
                ("public_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("linked_campaign_id", models.UUIDField(blank=True, null=True)),
                ("grade_code", models.CharField(blank=True, default="", max_length=3)),
                ("audience", models.CharField(blank=True, default="families", max_length=80)),
                ("created_by_user_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="surveys", to="core.school")),
            ],
            options={"ordering":["-updated_at"]},
        ),
        migrations.CreateModel(
            name="SurveyQuestion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("prompt", models.CharField(max_length=300)),
                ("question_type", models.CharField(choices=[("scale","Scale"),("choice","Choice"),("multi","Multiple Choice"),("text","Text"),("boolean","Boolean")], max_length=16)),
                ("key", models.CharField(max_length=64)),
                ("choices", models.JSONField(blank=True, default=list)),
                ("required", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("strategic_tags", models.JSONField(blank=True, default=list)),
                ("survey", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="survey_sentiment.surveydefinition")),
            ],
            options={"ordering":["sort_order","id"], "unique_together":{("survey","key")}},
        ),
        migrations.CreateModel(
            name="SurveyResponse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("household_id", models.UUIDField(blank=True, null=True)),
                ("application_id", models.UUIDField(blank=True, null=True)),
                ("student_id", models.UUIDField(blank=True, null=True)),
                ("campaign_id", models.UUIDField(blank=True, null=True)),
                ("anonymous", models.BooleanField(default=False)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("metadata_json", models.JSONField(blank=True, default=dict)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="survey_responses", to="core.school")),
                ("survey", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responses", to="survey_sentiment.surveydefinition")),
            ],
            options={"ordering":["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="SurveyAnswer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("value_json", models.JSONField(blank=True, default=dict)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="answers", to="survey_sentiment.surveyquestion")),
                ("response", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="survey_sentiment.surveyresponse")),
            ],
            options={"unique_together":{("response","question")}},
        ),
        migrations.AddIndex(model_name="surveydefinition", index=models.Index(fields=["school","purpose","status"], name="survey_sent_school__6b05a6_idx")),
        migrations.AddIndex(model_name="surveyresponse", index=models.Index(fields=["school","survey","submitted_at"], name="survey_sent_school__b0eb7a_idx")),
    ]
