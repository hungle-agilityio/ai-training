from dataclasses import dataclass
from datetime import datetime

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce

from reviews.models import Branch
from reviews.repositories import BAD_RATINGS, REPLY_WINDOW

STARS = (5, 4, 3, 2, 1)


@dataclass(frozen=True)
class CompareTotals:
    branch_id: int
    name: str
    review_count: int
    rating_total: int
    star_counts: tuple[int, int, int, int, int]  # 5 stars down to 1 star
    bad_counted: int
    bad_replied_in_time: int


def compare_totals(
    branch_ids: tuple[int, int], created_from: datetime | None, now: datetime
) -> list[CompareTotals]:
    """Totals of the given locations in one query, ordered by id; none drops out of the period.

    The period is a condition on every count, not a filter on the join, so a location with no
    review in the period still comes back, with zeros.
    """
    in_period = Q() if created_from is None else Q(reviews__created_at__gte=created_from)
    bad = in_period & Q(reviews__rating__range=BAD_RATINGS)
    has_reply = Q(reviews__reply__isnull=False)
    counted = bad & (has_reply | Q(reviews__created_at__lt=now - REPLY_WINDOW))
    in_time = (
        bad & has_reply & Q(reviews__reply__created_at__lte=F("reviews__created_at") + REPLY_WINDOW)
    )

    def stars(star: int) -> Count:
        return Count("reviews", filter=in_period & Q(reviews__rating=star))

    rows = (
        Branch.objects.filter(pk__in=branch_ids)
        .order_by("id")
        .values("id", "name")
        .annotate(
            review_count=Count("reviews", filter=in_period),
            rating_total=Coalesce(Sum("reviews__rating", filter=in_period), 0),
            bad_counted=Count("reviews", filter=counted),
            bad_replied_in_time=Count("reviews", filter=in_time),
            stars_5=stars(5),
            stars_4=stars(4),
            stars_3=stars(3),
            stars_2=stars(2),
            stars_1=stars(1),
        )
    )
    return [
        CompareTotals(
            branch_id=int(row["id"]),
            name=str(row["name"]),
            review_count=int(row["review_count"]),
            rating_total=int(row["rating_total"]),
            star_counts=(
                int(row["stars_5"]),
                int(row["stars_4"]),
                int(row["stars_3"]),
                int(row["stars_2"]),
                int(row["stars_1"]),
            ),
            bad_counted=int(row["bad_counted"]),
            bad_replied_in_time=int(row["bad_replied_in_time"]),
        )
        for row in rows
    ]
