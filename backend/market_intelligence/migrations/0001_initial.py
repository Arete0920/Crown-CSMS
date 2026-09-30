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
            name="MarketStudy",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=180)),
                ("status", models.CharField(choices=[("draft","Draft"),("ready","Ready"),("active","Active"),("archived","Archived")], db_index=True, default="draft", max_length=20)),
                ("analysis_year", models.PositiveIntegerField()),
                ("geography", models.JSONField(blank=True, default=dict)),
                ("population", models.JSONField(blank=True, default=dict)),
                ("economics", models.JSONField(blank=True, default=dict)),
                ("education_market", models.JSONField(blank=True, default=dict)),
                ("faith_community", models.JSONField(blank=True, default=dict)),
                ("competition", models.JSONField(blank=True, default=dict)),
                ("internal_context", models.JSONField(blank=True, default=dict)),
                ("strategic_objectives", models.JSONField(blank=True, default=dict)),
                ("source_provenance", models.JSONField(blank=True, default=list)),
                ("created_by_user_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_studies", to="core.school")),
            ],
            options={"ordering":["-analysis_year","-updated_at"]},
        ),
        migrations.CreateModel(
            name="StrategicRecommendation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("category", models.CharField(choices=[("tuition","Tuition"),("affordability","Affordability"),("financial_aid","Financial Aid"),("enrollment","Enrollment"),("program","Program"),("marketing","Marketing"),("transportation","Transportation"),("expansion","Expansion")], max_length=24)),
                ("priority", models.CharField(choices=[("low","Low"),("medium","Medium"),("high","High")], default="medium", max_length=12)),
                ("title", models.CharField(max_length=180)),
                ("rationale", models.TextField()),
                ("evidence", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(default="proposed", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="strategic_market_recommendations", to="core.school")),
                ("study", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to="market_intelligence.marketstudy")),
            ],
            options={"ordering":["-created_at"]},
        ),
        migrations.CreateModel(
            name="MarketStudyWizardSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("draft","Draft"),("configured","Configured"),("review","Review"),("committed","Committed")], db_index=True, default="draft", max_length=20)),
                ("current_step", models.PositiveSmallIntegerField(default=1)),
                ("draft_data", models.JSONField(blank=True, default=dict)),
                ("created_by_user_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("committed_study", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="wizard_sessions", to="market_intelligence.marketstudy")),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_study_wizard_sessions", to="core.school")),
            ],
            options={"ordering":["-updated_at"]},
        ),
        migrations.AddIndex(model_name="marketstudy", index=models.Index(fields=["school","status"], name="market_inte_school__a285a4_idx")),
        migrations.AddIndex(model_name="marketstudy", index=models.Index(fields=["school","analysis_year"], name="market_inte_school__2ceb86_idx")),
        migrations.AddIndex(model_name="strategicrecommendation", index=models.Index(fields=["school","category","priority"], name="market_inte_school__c791e6_idx")),
        migrations.AddIndex(model_name="marketstudywizardsession", index=models.Index(fields=["school","status"], name="market_inte_school__f7812c_idx")),
    ]
