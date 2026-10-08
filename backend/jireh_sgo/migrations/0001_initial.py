import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="SGOOrganization", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("legal_name", models.CharField(max_length=240)),
            ("state_of_domicile", models.CharField(max_length=2)),
            ("active", models.BooleanField(default=False)),
            ("federal_listing_verified", models.BooleanField(default=False)),
            ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
        ]),
        migrations.CreateModel(name="SGOMembership", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("role", models.CharField(max_length=16, choices=[("VIEWER","Viewer"),("REVIEWER","Reviewer"),("ADMIN","Administrator")])),
            ("active", models.BooleanField(default=False)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="memberships", to="jireh_sgo.sgoorganization")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sgo_memberships", to=settings.AUTH_USER_MODEL)),
        ], options={"constraints": [models.UniqueConstraint(fields=["organization", "user"], name="unique_sgo_member_user")]}),
        migrations.CreateModel(name="SGOProgram", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("name", models.CharField(max_length=200)),
            ("code", models.SlugField(max_length=70)),
            ("calendar_year", models.PositiveIntegerField()),
            ("funding_source", models.CharField(max_length=20, choices=[("FEDERAL_25F","Federal 25F"),("STATE","State"),("PRIVATE","Private")])),
            ("eligibility_rule_version", models.CharField(max_length=80)),
            ("status", models.CharField(max_length=12, default="PILOT", choices=[("PILOT","Pilot - no live settlement"),("ENABLED","Enabled")])),
            ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="programs", to="jireh_sgo.sgoorganization")),
        ], options={"constraints":[models.UniqueConstraint(fields=["organization","code","calendar_year"], name="unique_sgo_program_year")]}),
        migrations.CreateModel(name="SGOApplication", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("student_key", models.UUIDField()),
            ("school_key", models.UUIDField()),
            ("eligibility", models.CharField(max_length=16, default="UNREVIEWED", choices=[("UNREVIEWED","Unreviewed"),("ELIGIBLE","Reviewer attested eligible"),("INELIGIBLE","Reviewer attested ineligible")])),
            ("reviewer_evidence_key", models.CharField(blank=True, max_length=80)),
            ("reviewed_at", models.DateTimeField(blank=True, null=True)),
            ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="jireh_sgo.sgoorganization")),
            ("program", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="jireh_sgo.sgoprogram")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
        ], options={"constraints":[models.UniqueConstraint(fields=["organization","program","student_key"],name="unique_sgo_application_student")]}),
        migrations.CreateModel(name="SGOAward", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("amount_cents", models.PositiveBigIntegerField()),
            ("status", models.CharField(max_length=16, default="COMMITTED", choices=[("COMMITTED","Committed but not funded"),("CANCELLED","Cancelled")])),
            ("committed_at", models.DateTimeField(default=django.utils.timezone.now)),
            ("application", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="award", to="jireh_sgo.sgoapplication")),
            ("authorized_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="awards", to="jireh_sgo.sgoorganization")),
        ], options={"constraints":[models.CheckConstraint(condition=models.Q(("amount_cents__gt",0)), name="sgo_award_amount_positive")]}),
        migrations.CreateModel(name="SGOAuditEvent", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("action", models.CharField(max_length=70)),
            ("subject_key", models.UUIDField()),
            ("metadata", models.JSONField(blank=True, default=dict)),
            ("happened_at", models.DateTimeField(default=django.utils.timezone.now)),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="jireh_sgo.sgoorganization")),
        ], options={"indexes":[models.Index(fields=["organization","happened_at"],name="sgo_audit_org_time")]}),
    ]
