"""Separate hosted fictional household/SGO partner mappings; no data seeding."""
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("sandbox_demo", "0005_sandboxbuyerworkspace"),
        ("core", "0001_initial"),
        ("jireh_sgo", "0002_fictional_family_intake"),
    ]
    operations = [
        migrations.CreateModel(
            name="SandboxBuyerAidFamily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("family", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="fictional_buyer_aid_family", to="core.family")),
                ("guardian", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="fictional_buyer_guardian", to="core.guardian")),
                ("workspace", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="fictional_aid_family", to="sandbox_demo.sandboxbuyerworkspace")),
            ]),
        migrations.CreateModel(
            name="SandboxBuyerSGOPartner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("organization", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="fictional_buyer_partner", to="jireh_sgo.sgoorganization")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="fictional_sgo_partners", to="sandbox_demo.sandboxbuyerworkspace")),
            ]),
        migrations.CreateModel(
            name="SandboxBuyerSGOProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("partner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="programs", to="sandbox_demo.sandboxbuyersgopartner")),
                ("program", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="sandbox_buyer_program", to="jireh_sgo.sgoprogram")),
            ]),
        migrations.AddConstraint(
            model_name="sandboxbuyersgopartner",
            constraint=models.UniqueConstraint(fields=("workspace", "organization"), name="unique_buyer_sgo_partner"),
        ),
    ]
