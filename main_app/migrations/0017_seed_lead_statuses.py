"""
Seed the LeadStatus table with the default statuses that were previously hardcoded.
"""
from django.db import migrations


INITIAL_STATUSES = [
    {'code': 'NEW',           'name': 'New',           'color': 'info',    'is_system': True,  'sort_order': 10},
    {'code': 'CONTACTED',     'name': 'Contacted',     'color': 'warning', 'is_system': False, 'sort_order': 20},
    {'code': 'QUALIFIED',     'name': 'Qualified',     'color': 'primary', 'is_system': False, 'sort_order': 30},
    {'code': 'PROPOSAL_SENT', 'name': 'Proposal Sent', 'color': 'info',    'is_system': False, 'sort_order': 40},
    {'code': 'NEGOTIATION',   'name': 'Negotiation',   'color': 'warning', 'is_system': False, 'sort_order': 50},
    {'code': 'CLOSED_WON',    'name': 'Closed Won',    'color': 'success', 'is_system': True,  'sort_order': 60},
    {'code': 'CLOSED_LOST',   'name': 'Closed Lost',   'color': 'danger',  'is_system': True,  'sort_order': 70},
    {'code': 'TRANSFERRED',   'name': 'Transferred',   'color': 'secondary', 'is_system': True, 'sort_order': 80},
]


def seed_statuses(apps, schema_editor):
    LeadStatus = apps.get_model('main_app', 'LeadStatus')
    for status_data in INITIAL_STATUSES:
        LeadStatus.objects.get_or_create(
            code=status_data['code'],
            defaults=status_data,
        )


def reverse_seed(apps, schema_editor):
    LeadStatus = apps.get_model('main_app', 'LeadStatus')
    codes = [s['code'] for s in INITIAL_STATUSES]
    LeadStatus.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main_app', '0016_add_leadstatus_model'),
    ]

    operations = [
        migrations.RunPython(seed_statuses, reverse_seed),
    ]
