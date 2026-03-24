"""
Seed ActivityType and NextAction tables with default entries.
"""
from django.db import migrations


INITIAL_ACTIVITY_TYPES = [
    {'code': 'CALL',      'name': 'Phone Call',     'icon': 'fas fa-phone',          'color': 'info',    'is_system': True,  'sort_order': 10},
    {'code': 'EMAIL',     'name': 'Email',          'icon': 'fas fa-envelope',       'color': 'primary', 'is_system': True,  'sort_order': 20},
    {'code': 'MEETING',   'name': 'Meeting',        'icon': 'fas fa-handshake',      'color': 'success', 'is_system': True,  'sort_order': 30},
    {'code': 'PROPOSAL',  'name': 'Proposal Sent',  'icon': 'fas fa-file-alt',       'color': 'warning', 'is_system': False, 'sort_order': 40},
    {'code': 'FOLLOW_UP', 'name': 'Visit',          'icon': 'fas fa-calendar-check', 'color': 'success', 'is_system': True,  'sort_order': 50},
    {'code': 'TRANSFER',  'name': 'Lead Transfer',  'icon': 'fas fa-exchange-alt',   'color': 'secondary', 'is_system': True, 'sort_order': 60},
    {'code': 'NOTE',      'name': 'Note',           'icon': 'fas fa-sticky-note',    'color': 'dark',    'is_system': False, 'sort_order': 70},
]

INITIAL_NEXT_ACTIONS = [
    {'code': 'CALLBACK',       'name': 'Callback',          'is_system': False, 'sort_order': 10},
    {'code': 'SEND_BROCHURE',  'name': 'Send Brochure',     'is_system': False, 'sort_order': 20},
    {'code': 'SCHEDULE_VISIT', 'name': 'Schedule Visit',    'is_system': False, 'sort_order': 30},
    {'code': 'SEND_PROPOSAL',  'name': 'Send Proposal',     'is_system': False, 'sort_order': 40},
    {'code': 'FOLLOW_UP',      'name': 'Follow Up',         'is_system': False, 'sort_order': 50},
    {'code': 'CLOSE_DEAL',     'name': 'Close Deal',        'is_system': False, 'sort_order': 60},
    {'code': 'NO_ACTION',      'name': 'No Further Action', 'is_system': False, 'sort_order': 70},
]


def seed(apps, schema_editor):
    ActivityType = apps.get_model('main_app', 'ActivityType')
    NextAction = apps.get_model('main_app', 'NextAction')
    for data in INITIAL_ACTIVITY_TYPES:
        ActivityType.objects.get_or_create(code=data['code'], defaults=data)
    for data in INITIAL_NEXT_ACTIONS:
        NextAction.objects.get_or_create(code=data['code'], defaults=data)


def reverse_seed(apps, schema_editor):
    ActivityType = apps.get_model('main_app', 'ActivityType')
    NextAction = apps.get_model('main_app', 'NextAction')
    codes_at = [d['code'] for d in INITIAL_ACTIVITY_TYPES]
    codes_na = [d['code'] for d in INITIAL_NEXT_ACTIONS]
    ActivityType.objects.filter(code__in=codes_at).delete()
    NextAction.objects.filter(code__in=codes_na).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main_app', '0018_add_activitytype_nextaction'),
    ]

    operations = [
        migrations.RunPython(seed, reverse_seed),
    ]
