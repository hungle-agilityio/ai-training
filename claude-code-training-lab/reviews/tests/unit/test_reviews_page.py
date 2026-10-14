from datetime import UTC, datetime, timedelta

import pytest

from reviews.forms import PageForm
from reviews.models import Branch, Business, Review
from reviews.services import reviews_page, shorten_text


def _make_reviews(count: int, same_time: bool = False) -> list[Review]:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Downtown")
    base = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)
    Review.objects.bulk_create(
        Review(
            branch=branch,
            rating=(index % 5) + 1,
            text=f"review {index}",
            created_at=base if same_time else base - timedelta(minutes=index),
        )
        for index in range(count)
    )
    return list(Review.objects.order_by("id"))


def test_shorten_text_keeps_short_text() -> None:
    assert shorten_text("a" * 120) == ("a" * 120, False)


def test_shorten_text_cuts_long_text_with_ellipsis() -> None:
    short, was_cut = shorten_text("a" * 121)

    assert was_cut is True
    assert short == "a" * 120 + "…"


@pytest.mark.django_db
def test_first_page_has_twenty_newest_reviews() -> None:
    _make_reviews(45)

    page = reviews_page(None)

    assert len(page.rows) == 20
    assert page.rows[0].text == "review 0"
    assert (page.number, page.num_pages, page.total) == (1, 3, 45)
    assert (page.start_index, page.end_index) == (1, 20)
    assert page.has_previous is False
    assert page.has_next is True


@pytest.mark.django_db
def test_last_page_has_the_remaining_reviews() -> None:
    _make_reviews(45)

    page = reviews_page(3)

    assert len(page.rows) == 5
    assert (page.start_index, page.end_index) == (41, 45)
    assert page.has_previous is True
    assert page.has_next is False


@pytest.mark.django_db
def test_page_beyond_the_end_falls_back_to_last() -> None:
    _make_reviews(45)

    assert reviews_page(9999).number == 3


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2", 2), ("9999", 9999), ("", None), ("abc", None), ("0", None), ("-2", None), ("1.5", None)],
)
def test_page_form_accepts_only_positive_whole_numbers(value: str, expected: int | None) -> None:
    form = PageForm({"page": value})

    assert form.page_number() == expected


@pytest.mark.django_db
def test_order_is_stable_when_reviews_share_a_timestamp() -> None:
    _make_reviews(45, same_time=True)

    seen = [row.text for number in (1, 2, 3) for row in reviews_page(number).rows]

    assert len(seen) == 45
    assert len(set(seen)) == 45


@pytest.mark.django_db
def test_page_without_reviews_is_empty() -> None:
    page = reviews_page(None)

    assert page.rows == []
    assert (page.total, page.num_pages, page.number) == (0, 1, 1)
    assert (page.start_index, page.end_index) == (0, 0)


@pytest.mark.django_db
def test_row_has_sentiment_and_shortened_text() -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Airport")
    Review.objects.create(
        branch=branch, rating=2, text="x" * 150, created_at=datetime(2026, 10, 14, tzinfo=UTC)
    )

    row = reviews_page(None).rows[0]

    assert row.branch_name == "Airport"
    assert row.sentiment == "negative"
    assert row.rating_percent == 40
    assert row.is_truncated is True
    assert row.text == "x" * 150
    assert row.text_short == "x" * 120 + "…"


@pytest.mark.django_db
def test_page_links_use_ellipsis_for_many_pages() -> None:
    _make_reviews(400)

    links = reviews_page(10).links

    assert any(link.number is None for link in links)
    assert [link.number for link in links if link.is_current] == [10]
    assert links[0].number == 1
    assert links[-1].number == 20
