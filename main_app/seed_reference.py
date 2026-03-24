"""
Default LeadStatus, ActivityType, and NextAction rows (same as migrations 0017 / 0019).
Use via: python manage.py seed_crm_reference
"""
from typing import Any, Dict, List

LEAD_STATUS_SEEDS: List[Dict[str, Any]] = [
    {"code": "NEW", "name": "New", "color": "info", "is_system": True, "sort_order": 10},
    {"code": "CONTACTED", "name": "Contacted", "color": "warning", "is_system": False, "sort_order": 20},
    {"code": "QUALIFIED", "name": "Qualified", "color": "primary", "is_system": False, "sort_order": 30},
    {"code": "PROPOSAL_SENT", "name": "Proposal Sent", "color": "info", "is_system": False, "sort_order": 40},
    {"code": "NEGOTIATION", "name": "Negotiation", "color": "warning", "is_system": False, "sort_order": 50},
    {"code": "CLOSED_WON", "name": "Closed Won", "color": "success", "is_system": True, "sort_order": 60},
    {"code": "CLOSED_LOST", "name": "Closed Lost", "color": "danger", "is_system": True, "sort_order": 70},
    {"code": "TRANSFERRED", "name": "Transferred", "color": "secondary", "is_system": True, "sort_order": 80},
]

ACTIVITY_TYPE_SEEDS: List[Dict[str, Any]] = [
    {"code": "CALL", "name": "Phone Call", "icon": "fas fa-phone", "color": "info", "is_system": True, "sort_order": 10},
    {"code": "EMAIL", "name": "Email", "icon": "fas fa-envelope", "color": "primary", "is_system": True, "sort_order": 20},
    {"code": "MEETING", "name": "Meeting", "icon": "fas fa-handshake", "color": "success", "is_system": True, "sort_order": 30},
    {"code": "PROPOSAL", "name": "Proposal Sent", "icon": "fas fa-file-alt", "color": "warning", "is_system": False, "sort_order": 40},
    {"code": "FOLLOW_UP", "name": "Visit", "icon": "fas fa-calendar-check", "color": "success", "is_system": True, "sort_order": 50},
    {"code": "TRANSFER", "name": "Lead Transfer", "icon": "fas fa-exchange-alt", "color": "secondary", "is_system": True, "sort_order": 60},
    {"code": "NOTE", "name": "Note", "icon": "fas fa-sticky-note", "color": "dark", "is_system": False, "sort_order": 70},
]

NEXT_ACTION_SEEDS: List[Dict[str, Any]] = [
    {"code": "CALLBACK", "name": "Callback", "is_system": False, "sort_order": 10},
    {"code": "SEND_BROCHURE", "name": "Send Brochure", "is_system": False, "sort_order": 20},
    {"code": "SCHEDULE_VISIT", "name": "Schedule Visit", "is_system": False, "sort_order": 30},
    {"code": "SEND_PROPOSAL", "name": "Send Proposal", "is_system": False, "sort_order": 40},
    {"code": "FOLLOW_UP", "name": "Follow Up", "is_system": False, "sort_order": 50},
    {"code": "CLOSE_DEAL", "name": "Close Deal", "is_system": False, "sort_order": 60},
    {"code": "NO_ACTION", "name": "No Further Action", "is_system": False, "sort_order": 70},
]


def seed_lead_statuses():
    from .models import LeadStatus

    created = 0
    for row in LEAD_STATUS_SEEDS:
        _, was_created = LeadStatus.objects.get_or_create(code=row["code"], defaults=row)
        if was_created:
            created += 1
    return created


def seed_activity_types():
    from .models import ActivityType

    created = 0
    for row in ACTIVITY_TYPE_SEEDS:
        _, was_created = ActivityType.objects.get_or_create(code=row["code"], defaults=row)
        if was_created:
            created += 1
    return created


def seed_next_actions():
    from .models import NextAction

    created = 0
    for row in NEXT_ACTION_SEEDS:
        _, was_created = NextAction.objects.get_or_create(code=row["code"], defaults=row)
        if was_created:
            created += 1
    return created


def seed_all():
    """Idempotent: only inserts missing codes; does not delete or overwrite existing rows."""
    return {
        "lead_statuses": seed_lead_statuses(),
        "activity_types": seed_activity_types(),
        "next_actions": seed_next_actions(),
    }
