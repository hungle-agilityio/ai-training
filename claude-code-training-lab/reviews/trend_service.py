from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from reviews import trend_repository
from reviews.services import VIETNAM_TZ, average_from_totals

TREND_WEEKS = 8


@dataclass(frozen=True)
class WeekPoint:
    monday: date
    label: str
    review_count: int
    average_rating: float | None
    bar_percent: int


def weekly_trend(branch_id: int, now: datetime) -> list[WeekPoint]:
    """The last TREND_WEEKS Vietnam weeks of a location, oldest first, current week last."""
    today = now.astimezone(VIETNAM_TZ).date()
    last_monday = today - timedelta(days=today.weekday())
    mondays = [last_monday - timedelta(weeks=back) for back in range(TREND_WEEKS - 1, -1, -1)]
    start = datetime.combine(mondays[0], time.min, tzinfo=VIETNAM_TZ)
    end = datetime.combine(last_monday + timedelta(weeks=1), time.min, tzinfo=VIETNAM_TZ)

    counts = dict.fromkeys(mondays, 0)
    totals = dict.fromkeys(mondays, 0)
    for row in trend_repository.day_totals(branch_id, start, end, VIETNAM_TZ):
        monday = row.day - timedelta(days=row.day.weekday())
        counts[monday] += row.review_count
        totals[monday] += row.rating_total

    points = []
    for monday in mondays:
        average = average_from_totals(totals[monday], counts[monday])
        points.append(
            WeekPoint(
                monday=monday,
                label=f"{monday:%b} {monday.day}",
                review_count=counts[monday],
                average_rating=average,
                bar_percent=round(average / 5 * 100) if average is not None else 0,
            )
        )
    return points
