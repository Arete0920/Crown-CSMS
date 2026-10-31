"""Child custody release schema isolated from Extended Care's draft migration."""
import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("aftercare","0009_diadem_checkin_foundation"),
                  ("core","0021_diadem_custody_release_permission"),
                  migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="DaycareRelease",fields=[
            ("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ("school",models.ForeignKey("core.School",on_delete=django.db.models.deletion.PROTECT)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("attendance",models.OneToOneField("aftercare.DaycareAttendance",on_delete=django.db.models.deletion.PROTECT,related_name="custody_release")),
            ("site",models.ForeignKey("aftercare.DaycareSite",on_delete=django.db.models.deletion.PROTECT,related_name="custody_releases")),
            ("room",models.ForeignKey("aftercare.DaycareRoom",on_delete=django.db.models.deletion.PROTECT,related_name="custody_releases")),
            ("child",models.ForeignKey("aftercare.DaycareChild",on_delete=django.db.models.deletion.PROTECT,related_name="custody_releases")),
            ("guardian_authority",models.ForeignKey("aftercare.DaycareGuardianAuthority",on_delete=django.db.models.deletion.PROTECT,related_name="custody_releases")),
            ("actor",models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name="daycare_releases_performed")),
            ("released_at",models.DateTimeField()),
            ("identity_method",models.CharField(max_length=32,choices=[
                ("GOVERNMENT_PHOTO_ID","Government photo ID"),
                ("APPROVED_PHOTO_ROSTER","Approved photo roster"),
                ("PERSONALLY_KNOWN","Personally known to releasing staff")])),
            ("identity_verified",models.BooleanField(default=False)),
            ("guardian_name_snapshot",models.CharField(max_length=180)),
            ("request_key",models.UUIDField(default=uuid.uuid4)),
        ],options={"constraints":[
            models.UniqueConstraint(fields=["school","request_key"],name="dia_release_retry_uq"),
            models.CheckConstraint(condition=models.Q(identity_verified=True),name="dia_release_id_verified_ck"),
            models.CheckConstraint(condition=models.Q(identity_method__in=["APPROVED_PHOTO_ROSTER","GOVERNMENT_PHOTO_ID","PERSONALLY_KNOWN"]),name="dia_release_method_ck"),
        ],"indexes":[
            models.Index(fields=["school","room","released_at"],name="dia_release_room_at_idx"),
            models.Index(fields=["school","child","released_at"],name="dia_release_child_at_idx"),
        ]}),
    ]
