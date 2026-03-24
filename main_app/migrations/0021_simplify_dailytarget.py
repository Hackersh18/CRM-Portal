from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0020_add_dailytarget'),
    ]

    operations = [
        # Remove old fields from DailyTarget
        migrations.RemoveField(model_name='dailytarget', name='title'),
        migrations.RemoveField(model_name='dailytarget', name='description'),
        migrations.RemoveField(model_name='dailytarget', name='target_type'),
        migrations.RemoveField(model_name='dailytarget', name='status_filter'),
        migrations.RemoveField(model_name='dailytarget', name='priority'),

        # Change target_count from IntegerField(default=0) to PositiveIntegerField (required)
        migrations.AlterField(
            model_name='dailytarget',
            name='target_count',
            field=models.PositiveIntegerField(help_text='Total tasks to show (e.g. 100)'),
        ),

        # Simplify ordering
        migrations.AlterModelOptions(
            name='dailytarget',
            options={'ordering': ['-target_date']},
        ),

        # Remove old fields from DailyTargetAssignment
        migrations.RemoveField(model_name='dailytargetassignment', name='status'),
        migrations.RemoveField(model_name='dailytargetassignment', name='notes'),

        # Remove old ordering & unique_together, set new
        migrations.AlterModelOptions(
            name='dailytargetassignment',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='dailytargetassignment',
            unique_together={('target', 'counsellor')},
        ),
    ]
