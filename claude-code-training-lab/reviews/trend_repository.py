from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from reviews.models import Review


@dataclass(frozen=True)
class DayTotals:
    day: date
    review_count: int
    rating_total: int


def day_totals(branch_id: int, start: datetime, end: datetime, tz: ZoneInfo) -> list[DayTotals]:
    """Review count and rating sum per calendar day of `tz` in [start, end), in one query."""
    rows = (
        Review.objects.filter(branch_id=branch_id, created_at__gte=start, created_at__lt=end)
        .annotate(day=TruncDate("created_at", tzinfo=tz))
        .order_by("day")
        .values("day")
        .annotate(review_count=Count("id"), rating_total=Sum("rating"))
    )
    return [
        DayTotals(
            day=row["day"],
            review_count=int(row["review_count"]),
            rating_total=int(row["rating_total"]),
        )
        for row in rows
    ]
