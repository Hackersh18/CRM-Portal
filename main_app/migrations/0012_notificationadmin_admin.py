from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0011_alter_admin_id_alter_business_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationadmin',
            name='admin',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='admin_notifications',
                to='main_app.customuser',
            ),
        ),
    ]
