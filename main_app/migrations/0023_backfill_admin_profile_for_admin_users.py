from django.db import migrations


def forwards(apps, schema_editor):
    CustomUser = apps.get_model("main_app", "CustomUser")
    Admin = apps.get_model("main_app", "Admin")
    for user in CustomUser.objects.iterator():
        if str(getattr(user, "user_type", "") or "") != "1":
            continue
        if Admin.objects.filter(admin_id=user.pk).exists():
            continue
        is_super = bool(getattr(user, "is_superuser", False))
        Admin.objects.create(
            admin_id=user.pk,
            is_superadmin=is_super,
            can_delete=True,
            can_view_performance=True,
            can_view_counsellor_work=True,
            can_manage_settings=True,
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0022_add_admin_permissions"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
