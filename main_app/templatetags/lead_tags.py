import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

_BOOTSTRAP_BADGE_COLORS = frozenset(
    {'primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark', 'pink'}
)


def _safe_badge_color(value):
    c = (value or 'secondary').strip().lower()
    return c if c in _BOOTSTRAP_BADGE_COLORS else 'secondary'


def _safe_fa_icon_class(value):
    s = (value or '').strip()
    if s and re.match(r'^[a-zA-Z0-9\s\-_]+$', s) and '..' not in s:
        return s
    return 'fas fa-tasks'


@register.simple_tag(takes_context=True)
def status_badge(context, status_code):
    """
    Render a Bootstrap badge for a lead status code.
    Uses the lead_status_map from the context processor.
    Usage: {% status_badge lead.status %}
    """
    status_map = context.get('lead_status_map', {})
    info = status_map.get(status_code)
    if info:
        color = _safe_badge_color(info.get('color'))
        name = escape(str(info.get('name', '')))
        return mark_safe(f'<span class="badge badge-{color}">{name}</span>')
    return mark_safe(f'<span class="badge badge-secondary">{escape(str(status_code))}</span>')


@register.filter
def dict_get(d, key):
    """Lookup a key in a dict. Usage: {{ my_dict|dict_get:key_var }}"""
    if isinstance(d, dict):
        return d.get(key, key)
    return key


@register.simple_tag
def activity_type_badge(code):
    """Render activity type badge from DB. Usage: {% activity_type_badge activity.activity_type %}"""
    try:
        from main_app.models import ActivityType
        obj = ActivityType.objects.filter(code=code).first()
        if obj:
            color = _safe_badge_color(obj.color)
            icon = _safe_fa_icon_class(obj.icon)
            name = escape(str(obj.name))
            return mark_safe(f'<span class="badge badge-{color}"><i class="{icon} mr-1"></i>{name}</span>')
    except Exception:
        pass
    return mark_safe(f'<span class="badge badge-info">{escape(str(code))}</span>')


@register.simple_tag
def next_action_name(code):
    """Return the display name for a next-action code. Usage: {% next_action_name activity.next_action %}"""
    if not code:
        return '—'
    try:
        from main_app.models import NextAction
        obj = NextAction.objects.filter(code=code).first()
        if obj:
            return obj.name
    except Exception:
        pass
    return code
