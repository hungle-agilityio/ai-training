from datetime import datetime

from django import template
from django.utils import timezone
from django.utils.formats import date_format

register = template.Library()

RELATIVE_LIMIT_DAYS = 7
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400


def _ago(count: int, unit: str) -> str:
    return f"{count} {unit}{'' if count == 1 else 's'} ago"


@register.filter
def relative_review_date(value: datetime, now: datetime | None = None) -> str:
    """Whole units since the review for under 7 days, else the Vietnam-time date."""
    current = now or timezone.now()
    seconds = int((current - value).total_seconds())
    if seconds < SECONDS_PER_MINUTE:
        return "just now"
    if seconds < SECONDS_PER_HOUR:
        return _ago(seconds // SECONDS_PER_MINUTE, "minute")
    if seconds < SECONDS_PER_DAY:
        return _ago(seconds // SECONDS_PER_HOUR, "hour")
    if seconds < RELATIVE_LIMIT_DAYS * SECONDS_PER_DAY:
        return _ago(seconds // SECONDS_PER_DAY, "day")
    return date_format(timezone.localtime(value), "M j, Y")


@register.filter
def full_review_date(value: datetime) -> str:
    """Vietnam time, 24-hour, no seconds."""
    return date_format(timezone.localtime(value), "M j, Y, H:i")
