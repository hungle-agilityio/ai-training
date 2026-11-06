import re
from datetime import UTC, datetime, timedelta

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews import repositories, services
from reviews.models import Branch, Business, Review, ReviewReply

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


def _review(branch: Branch, rating: int, age: timedelta, reply_after: timedelta | None) -> Review:
    created = NOW - age
    review = Review.objects.create(branch=branch, rating=rating, text="t", created_at=created)
    if reply_after is not None:
        ReviewReply.objects.create(
            review=review,
            text="r",
            created_at=created + reply_after,
            updated_at=created + reply_after,
        )
    return review


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="B"), name="Airport")


def _speed(now: datetime = NOW) -> services.DashboardOverview:
    return services.dashboard_overview(now=now)


@pytest.mark.django_db
def test_exactly_24_hours_counts_and_one_second_more_does_not(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=5), timedelta(hours=24))
    _review(branch, 2, timedelta(days=5), timedelta(hours=24, seconds=1))

    speed = _speed().reply_speed

    assert (speed.counted, speed.replied_in_time, speed.percent) == (2, 1, 50)


@pytest.mark.django_db
def test_unanswered_bad_review_23h_old_is_not_counted_25h_is_a_miss(branch: Branch) -> None:
    _review(branch, 1, timedelta(hours=23), None)
    assert _speed().reply_speed.counted == 0

    _review(branch, 1, timedelta(hours=25), None)
    speed = _speed().reply_speed
    assert (speed.counted, speed.replied_in_time, speed.percent) == (1, 0, 0)
    assert speed.average_label == ""


@pytest.mark.django_db
def test_good_reviews_are_ignored(branch: Branch) -> None:
    _review(branch, 5, timedelta(days=3), timedelta(hours=1))

    assert _speed().reply_speed.counted == 0
    assert _speed().branches[0].reply_percent is None


@pytest.mark.django_db
def test_average_is_over_replied_counted_reviews_and_uses_days(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=9), timedelta(hours=48))
    _review(branch, 2, timedelta(days=9), timedelta(hours=100))

    overview = _speed()

    assert overview.reply_speed.average_label == "3.1 days"
    assert overview.branches[0].reply_percent == 0


@pytest.mark.django_db
def test_dashboard_card_and_column_render(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=5), timedelta(hours=2))
    _review(branch, 1, timedelta(days=5), None)

    html = Client().get("/dashboard/").content.decode()

    assert 'id="kpi-reply-speed"' in html
    assert "Replied in 24h" in html
    assert "50%" in html
    assert "1 of 2 bad reviews" in html
    assert "Average reply time 2.0 h" in html
    assert 'id="location-scores"' in html


@pytest.mark.django_db
def test_dashboard_card_empty_state(branch: Branch) -> None:
    html = Client().get("/dashboard/").content.decode()

    assert "No bad reviews yet" in html
    assert "bad reviews</p>" not in html
    assert "Average reply time" not in html
    assert "No replies yet" not in html


def _location_scores_cells(html: str) -> tuple[list[str], list[str]]:
    panel = html.split('id="location-scores"')[1].split("</section>")[0]
    headers = re.findall(r'<th scope="col"[^>]*>([^<]*)</th>', panel)
    last_row = panel.split("<tbody>")[1]
    cells = re.findall(r"<td[^>]*>(.*?)</td>", last_row, flags=re.S)
    return headers, cells


@pytest.mark.django_db
def test_location_column_sits_between_status_and_details(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=5), timedelta(hours=2))

    headers, cells = _location_scores_cells(Client().get("/dashboard/").content.decode())

    assert headers[-3:] == ["Status", "Replied in 24h", "Details"]
    assert cells[-2] == "100%"


@pytest.mark.django_db
def test_location_without_counted_bad_review_shows_a_muted_dash(branch: Branch) -> None:
    _, cells = _location_scores_cells(Client().get("/dashboard/").content.decode())

    assert cells[-2] == '<span class="muted">&ndash;</span>'


@pytest.mark.django_db
def test_dashboard_card_none_replied(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=5), None)

    html = Client().get("/dashboard/").content.decode()

    assert "0 of 1 bad reviews" in html
    assert "No replies yet" in html


@pytest.mark.django_db
@pytest.mark.parametrize("locations", [20, 200])
def test_dashboard_query_count_does_not_grow(
    locations: int, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="B")
    for i in range(locations):
        b = Branch.objects.create(business=business, name=f"L{i}")
        _review(b, 1, timedelta(days=3), timedelta(hours=5))
        _review(b, 2, timedelta(days=3), None)

    with django_assert_num_queries(3):
        assert Client().get("/dashboard/").status_code == 200


@pytest.mark.django_db
def test_repository_totals_keep_one_row_per_branch(branch: Branch) -> None:
    _review(branch, 1, timedelta(days=5), timedelta(hours=2))

    totals = repositories.branch_rating_totals(now=NOW)

    assert len(totals) == 1
    assert totals[0].review_count == 1
    assert totals[0].reply_seconds == 7200.0


@pytest.mark.django_db
def test_demo_data_shows_the_numbers_of_the_spec() -> None:
    call_command("seed_demo_data")

    overview = services.dashboard_overview()

    speed = overview.reply_speed
    assert (speed.percent, speed.replied_in_time, speed.counted) == (50, 2, 4)
    assert speed.average_label == "17.7 h"
    assert {row.name: row.reply_percent for row in overview.branches} == {
        "Airport": 0,
        "Downtown": None,
        "Riverside": 100,
    }
