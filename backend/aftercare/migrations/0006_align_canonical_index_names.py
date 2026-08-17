from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("aftercare", "0005_canonical_extended_care_authority"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="aftercareattendance",
            old_name="aftercare_a_school__8d2340_idx",
            new_name="aftercare_a_school__964d7d_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercareenrollment",
            old_name="aftercare_e_school__c97659_idx",
            new_name="aftercare_a_school__44f36b_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercareenrollment",
            old_name="aftercare_e_school__874184_idx",
            new_name="aftercare_a_school__35f1d1_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercareincident",
            old_name="aftercare_i_school__4cb9ad_idx",
            new_name="aftercare_a_school__1779bc_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercareincident",
            old_name="aftercare_i_school__d41667_idx",
            new_name="aftercare_a_school__0f80a9_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercaremonthlychargerun",
            old_name="aftercare_m_school__3007e1_idx",
            new_name="aftercare_a_school__dd1420_idx",
        ),
        migrations.RenameIndex(
            model_name="aftercarepickupcontact",
            old_name="aftercare_p_school__458577_idx",
            new_name="aftercare_a_school__455a72_idx",
        ),
    ]
