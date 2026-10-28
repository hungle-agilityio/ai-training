from datetime import UTC, datetime

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

WEEK = "2026-10-14"  # week 12 to 18 October 2026, Vietnam time


def _review(branch: Branch, rating: int, text: str, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text=text, created_at=created_at)


@pytest.fixture
def branches() -> dict[str, Branch]:
    business = Business.objects.create(name="Demo")
    return {
        name: Branch.objects.create(business=business, name=name)
        for name in ("Airport", "Downtown", "Newtown")
    }


@pytest.fixture
def seeded(branches: dict[str, Branch]) -> dict[str, Branch]:
    in_week = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)
    for rating in (1, 2, 3, 4, 5):
        _review(branches["Airport"], rating, f"airport-{rating}", in_week)
    _review(branches["Downtown"], 1, "downtown-1", in_week)
    _review(branches["Airport"], 1, "airport-old", datetime(2026, 10, 5, 5, 0, tzinfo=UTC))
    return branches


def _get(query: str = "") -> str:
    response = Client().get(f"/reviews/{query}")
    assert response.status_code == 200
    return response.content.decode()


def _shown(content: str, *texts: str) -> set[str]:
    return {text for text in texts if f"{text}\n" in content or f">{text}<" in content}


ALL = ("airport-1", "airport-2", "airport-3", "airport-4", "airport-5", "downtown-1", "airport-old")


@pytest.mark.django_db
def test_form_starts_on_all_locations_and_all_ratings(seeded: dict[str, Branch]) -> None:
    content = _get()

    assert '<option value="" selected>All locations</option>' in content
    assert '<option value="" selected>All ratings</option>' in content
    assert 'name="week"' in content
    assert 'type="date"' in content
    assert 'name="page"' not in content
    for name in ("Airport", "Downtown", "Newtown"):
        assert f">{name}</option>" in content


@pytest.mark.django_db
def test_filters_narrow_the_list(seeded: dict[str, Branch]) -> None:
    assert _shown(_get("?rating=bad"), *ALL) == {
        "airport-1",
        "airport-2",
        "downtown-1",
        "airport-old",
    }
    assert _shown(_get("?rating=good"), *ALL) == {"airport-4", "airport-5"}
    assert "airport-3" in _shown(_get(), *ALL)
    assert _shown(_get(f"?location={seeded['Downtown'].id}"), *ALL) == {"downtown-1"}
    assert _shown(_get(f"?week={WEEK}&rating=bad"), *ALL) == {
        "airport-1",
        "airport-2",
        "downtown-1",
    }


@pytest.mark.django_db
def test_summary_week_label_and_chosen_values_are_shown(seeded: dict[str, Branch]) -> None:
    airport = seeded["Airport"]

    content = _get(f"?location={airport.id}&rating=bad&week={WEEK}")

    assert "Showing 1-2 of 2 reviews" in content
    assert "Week: Oct 12 - Oct 18, 2026" in content
    assert f'<option value="{airport.id}" selected>Airport</option>' in content
    assert '<option value="bad" selected>' in content
    assert f'value="{WEEK}"' in content


@pytest.mark.django_db
def test_no_match_shows_no_reviews_found_and_keeps_the_form(seeded: dict[str, Branch]) -> None:
    content = _get("?week=2025-03-05")

    assert "No reviews found" in content
    assert "No reviews yet" not in content
    assert "Showing 0-0" not in content
    assert 'name="week"' in content


@pytest.mark.django_db
def test_location_without_reviews_shows_no_reviews_found(seeded: dict[str, Branch]) -> None:
    assert "No reviews found" in _get(f"?location={seeded['Newtown'].id}")


@pytest.mark.django_db
def test_no_reviews_at_all_still_says_no_reviews_yet(branches: dict[str, Branch]) -> None:
    content = _get()

    assert "No reviews yet" in content
    assert "No reviews found" not in content


@pytest.mark.django_db
def test_next_link_keeps_the_filters(branches: dict[str, Branch]) -> None:
    for index in range(25):
        _review(
            branches["Airport"], 1, f"bad-{index}", datetime(2026, 10, 14, 5, index, tzinfo=UTC)
        )
    airport_id = branches["Airport"].id

    first = _get(f"?location={airport_id}&rating=bad&week={WEEK}")
    second = _get(f"?location={airport_id}&rating=bad&week={WEEK}&page=2")

    link = f'href="?location={airport_id}&amp;rating=bad&amp;week={WEEK}&amp;page=2"'
    assert link in first
    assert "Showing 1-20 of 25 reviews" in first
    assert "Showing 21-25 of 25 reviews" in second
    assert 'aria-disabled="true">Next' in second


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    ["?week=abc", "?week=2026-13-45", "?week=9999-12-31", "?rating=meh", "?location=999999"],
)
def test_wrong_filter_values_are_ignored(seeded: dict[str, Branch], query: str) -> None:
    content = _get(query)

    assert "Showing 1-7 of 7 reviews" in content
    assert "No reviews found" not in content


@pytest.mark.django_db
def test_dashboard_does_not_change_with_filters(seeded: dict[str, Branch]) -> None:
    seeded["Newtown"].delete()  # a location without reviews is a separate ticket
    plain = Client().get("/api/dashboard/").json()
    filtered = Client().get(f"/api/dashboard/?rating=bad&week={WEEK}").json()

    assert plain == filtered


@pytest.mark.django_db
def test_filtered_page_query_count(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    business = Business.objects.create(name="Demo")
    for index in range(20):
        branch = Branch.objects.create(business=business, name=f"Branch {index}")
        _review(branch, 1, "bad", datetime(2026, 10, 14, 5, 0, tzinfo=UTC))

    with django_assert_max_num_queries(3):
        response = Client().get(f"/reviews/?rating=bad&week={WEEK}&location=1")

    assert response.status_code == 200


@pytest.mark.django_db
def test_branch_name_is_escaped_in_the_location_list() -> None:
    business = Business.objects.create(name="Demo")
    Branch.objects.create(business=business, name="<script>alert(1)</script>")

    content = _get()

    assert "<script>alert(1)</script>" not in content
    assert "&lt;script&gt;" in content


@pytest.mark.django_db
def test_last_page_of_a_filtered_list_is_used_for_a_page_beyond_the_end(
    branches: dict[str, Branch],
) -> None:
    for index in range(25):
        _review(
            branches["Airport"], 1, f"bad-{index}", datetime(2026, 10, 14, 5, index, tzinfo=UTC)
        )

    assert "Showing 21-25 of 25 reviews" in _get("?rating=bad&page=9999")


@pytest.mark.django_db
def test_rating_dropdown_lists_good_bad_then_five_to_one_stars(seeded: dict[str, Branch]) -> None:
    content = _get()

    labels = [
        "All ratings",
        "Good (4-5 stars)",
        "Bad (1-2 stars)",
        "5 stars",
        "4 stars",
        "3 stars",
        "2 stars",
        "1 star",
    ]
    positions = [content.index(f">{label}</option>") for label in labels]
    assert positions == sorted(positions)
    assert content.count('name="rating"') == 1


@pytest.mark.django_db
@pytest.mark.parametrize("stars", [1, 2, 3, 4, 5])
def test_star_count_shows_only_reviews_with_exactly_that_rating(
    seeded: dict[str, Branch], stars: int
) -> None:
    content = _get(f"?rating={stars}")

    shown = _shown(content, *ALL)
    expected = {f"airport-{stars}"} | ({"downtown-1", "airport-old"} if stars == 1 else set())
    assert shown == expected
    assert f'<option value="{stars}" selected>' in content


@pytest.mark.django_db
def test_star_count_line_counts_only_matching_reviews(seeded: dict[str, Branch]) -> None:
    assert "Showing 1-3 of 3 reviews" in _get("?rating=1")


@pytest.mark.django_db
def test_good_and_bad_links_keep_working(seeded: dict[str, Branch]) -> None:
    assert _shown(_get("?rating=good"), *ALL) == {"airport-4", "airport-5"}
    assert _shown(_get("?rating=bad"), *ALL) == {
        "airport-1",
        "airport-2",
        "downtown-1",
        "airport-old",
    }


@pytest.mark.django_db
def test_star_count_combines_with_location_and_week(seeded: dict[str, Branch]) -> None:
    downtown = seeded["Downtown"].id

    content = _get(f"?rating=1&location={downtown}&week={WEEK}")

    assert _shown(content, *ALL) == {"downtown-1"}


@pytest.mark.django_db
def test_star_count_with_no_match_says_no_reviews_found(seeded: dict[str, Branch]) -> None:
    newtown = seeded["Newtown"].id

    content = _get(f"?rating=3&location={newtown}")

    assert "No reviews found" in content
    assert "No review matches these filters" in content
    assert _shown(content, *ALL) == set()


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["7", "0", "6", "-1", "abc"])
def test_unknown_rating_value_is_ignored(seeded: dict[str, Branch], value: str) -> None:
    content = _get(f"?rating={value}")

    assert _shown(content, *ALL) == set(ALL)
    assert '<option value="" selected>All ratings</option>' in content


@pytest.mark.django_db
def test_star_count_survives_paging(branches: dict[str, Branch]) -> None:
    when = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)
    for index in range(30):
        _review(branches["Airport"], 4, f"four-{index}", when)
    _review(branches["Airport"], 2, "two-only", when)

    content = _get("?rating=4&page=2")

    assert '<option value="4" selected>' in content
    assert 'href="?rating=4&amp;page=1"' in content
    assert "two-only" not in content


@pytest.mark.django_db
def test_star_count_combines_with_search(branches: dict[str, Branch]) -> None:
    when = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)
    for rating, text in ((1, "parking was awful"), (1, "billing mistake"), (3, "parking was fine")):
        create_review(branch=branches["Airport"], rating=rating, text=text, created_at=when)

    content = _get("?rating=1&search=parking")

    assert "parking was awful" in content
    assert "billing mistake" not in content
    assert "parking was fine" not in content
