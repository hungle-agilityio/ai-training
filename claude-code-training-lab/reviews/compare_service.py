from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from reviews import compare_repository
from reviews.compare_repository import STARS, CompareTotals
from reviews.services import RATING_RANGES, average_from_totals, reply_share_percent
from reviews.topic_service import percent

PERIOD_LABELS: dict[int | None, str] = {None: "All time", 30: "Last 30 days", 90: "Last 90 days"}


@dataclass(frozen=True)
class StarRow:
    stars: int
    count: int
    percent: int


@dataclass(frozen=True)
class LocationSide:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None
    good_percent: int | None
    bad_percent: int | None
    replied_in_time_percent: int | None
    star_rows: tuple[StarRow, ...]


@dataclass(frozen=True)
class Comparison:
    period_days: int | None
    period_label: str
    a: LocationSide
    b: LocationSide
    difference: float | None


def _share(count: int, whole: int) -> int | None:
    return percent(count, whole) if whole else None


def _side(totals: CompareTotals) -> LocationSide:
    count = totals.review_count
    by_star = dict(zip(STARS, totals.star_counts, strict=True))
    good_low, good_high = RATING_RANGES["good"]
    bad_low, bad_high = RATING_RANGES["bad"]
    good = sum(n for star, n in by_star.items() if good_low <= star <= good_high)
    bad = sum(n for star, n in by_star.items() if bad_low <= star <= bad_high)
    return LocationSide(
        branch_id=totals.branch_id,
        name=totals.name,
        review_count=count,
        average_rating=average_from_totals(totals.rating_total, count),
        good_percent=_share(good, count),
        bad_percent=_share(bad, count),
        replied_in_time_percent=reply_share_percent(totals.bad_replied_in_time, totals.bad_counted),
        star_rows=tuple(StarRow(star, n, percent(n, count)) for star, n in by_star.items()),
    )


def _difference(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    diff = Decimal(str(a)) - Decimal(str(b))
    return float(diff.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _label(period_days: int | None) -> str:
    return PERIOD_LABELS.get(period_days) or "Last " + str(period_days) + " days"


def compare_locations(
    a_id: int, b_id: int, period_days: int | None, now: datetime
) -> Comparison | None:
    """The numbers of the Compare page; None when an id is not a location or both are the same."""
    if a_id == b_id:
        return None
    created_from = now - timedelta(days=period_days) if period_days else None
    found = compare_repository.compare_totals((a_id, b_id), created_from, now)
    rows = {t.branch_id: t for t in found}
    if a_id not in rows or b_id not in rows:
        return None
    a, b = _side(rows[a_id]), _side(rows[b_id])
    return Comparison(
        period_days=period_days,
        period_label=_label(period_days),
        a=a,
        b=b,
        difference=_difference(a.average_rating, b.average_rating),
    )
