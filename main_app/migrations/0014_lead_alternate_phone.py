# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0013_alter_business_business_id_alter_lead_lead_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='alternate_phone',
            field=models.CharField(blank=True, max_length=15, verbose_name='Alternate Phone'),
        ),
    ]
