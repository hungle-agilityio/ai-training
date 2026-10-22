import logging
from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business
from reviews.repositories import create_review

BASE = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)
TOO_SHORT = "Type at least 3 characters to search."
NO_MATCH_HINT = (
    "No review matches these filters. Try other words, another location, rating or week."
)


def _get(query: str = "") -> str:
    response = Client().get(f"/reviews/{query}")
    assert response.status_code == 200
    return response.content.decode()


def _add(branch: Branch, rating: int, text: str, minutes: int = 0) -> None:
    create_review(
        branch=branch, rating=rating, text=text, created_at=BASE + timedelta(minutes=minutes)
    )


@pytest.fixture
def branches() -> dict[str, Branch]:
    business = Business.objects.create(name="Demo")
    return {
        name: Branch.objects.create(business=business, name=name)
        for name in ("Airport", "Riverside")
    }


@pytest.fixture
def parking(branches: dict[str, Branch]) -> dict[str, Branch]:
    _add(branches["Riverside"], 2, "No parking nearby", minutes=1)
    _add(branches["Airport"], 5, "Easy parking, friendly staff", minutes=2)
    _add(branches["Riverside"], 3, "Parking was full", minutes=3)
    for index in range(10):
        _add(branches["Airport"], 4, f"Other review {index}", minutes=10 + index)
    return branches


@pytest.mark.django_db
def test_search_shows_only_matching_reviews_and_their_count(parking: dict[str, Branch]) -> None:
    content = _get("?search=parking")

    assert "Showing 1-3 of 3 reviews" in content
    assert "Other review" not in content
    assert "Parking was full" in content


@pytest.mark.django_db
def test_next_link_keeps_the_search_and_the_form_has_no_page_field(
    branches: dict[str, Branch],
) -> None:
    for index in range(25):
        _add(branches["Airport"], 4, f"Parking spot {index}", minutes=index)
    _add(branches["Airport"], 4, "Something else", minutes=40)

    content = _get("?search=parking")

    assert 'href="?search=parking&amp;page=2"' in content
    assert 'name="page"' not in content
    assert 'value="parking"' in content
    assert "Showing 1-20 of 25 reviews" in content


@pytest.mark.django_db
def test_no_match_shows_the_hint_and_no_table(parking: dict[str, Branch]) -> None:
    content = _get("?search=elevator")

    assert "No reviews found" in content
    assert NO_MATCH_HINT in content
    assert "<table" not in content


@pytest.mark.django_db
def test_no_reviews_at_all_still_says_no_reviews_yet() -> None:
    assert "No reviews yet" in _get()


@pytest.mark.django_db
def test_empty_database_with_a_search_says_no_reviews_found() -> None:
    content = _get("?search=parking")

    assert "No reviews found" in content
    assert "No reviews yet" not in content


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["?search=", "?search=%20%20%20"])
def test_blank_search_shows_the_full_list_without_a_message(
    query: str, parking: dict[str, Branch]
) -> None:
    content = _get(query)

    assert TOO_SHORT not in content
    assert "Showing 1-13 of 13 reviews" in content
    assert ">Clear<" not in content


@pytest.mark.django_db
def test_too_short_search_shows_the_message_and_still_filters_other_fields(
    parking: dict[str, Branch],
) -> None:
    content = _get(f"?search=pa&location={parking['Riverside'].id}")

    assert TOO_SHORT in content
    assert "Showing 1-2 of 2 reviews" in content
    assert 'value="pa"' in content
    assert "search=" not in content.split('class="export-action"')[1].split("</div>")[0]


@pytest.mark.django_db
def test_clear_is_shown_for_a_too_short_search(parking: dict[str, Branch]) -> None:
    assert ">Clear<" in _get("?search=pa")


@pytest.mark.django_db
def test_search_box_is_the_first_field_with_label_hint_and_sensitive_mark(
    parking: dict[str, Branch],
) -> None:
    content = _get()

    assert content.index('id="filter-search"') < content.index('id="filter-location"')
    assert '<label for="filter-search">Search</label>' in content
    assert "Words in the review" in content
    assert 'type="search"' in content
    assert 'data-sensitive="search-term"' in content


@pytest.mark.django_db
def test_too_short_message_is_an_alert_outside_the_filter_form(
    parking: dict[str, Branch],
) -> None:
    content = _get("?search=pa")

    alert = content.index('role="alert"')
    assert content.index("</form>") < alert < content.index("Showing")
    assert TOO_SHORT in content[alert : alert + 200]
    assert content.count(TOO_SHORT) == 1


@pytest.mark.django_db
def test_apply_and_clear_are_one_group_with_their_own_colours(
    parking: dict[str, Branch],
) -> None:
    content = _get("?search=parking")

    group = content.split('class="filter-actions"')[1].split("</div>")[0]
    assert 'class="button button-apply"' in group
    assert 'class="button button-clear"' in group
    assert group.index("button-apply") < group.index("button-clear")


@pytest.mark.django_db
def test_without_a_filter_only_apply_is_in_the_group(parking: dict[str, Branch]) -> None:
    group = _get().split('class="filter-actions"')[1].split("</div>")[0]

    assert "button-apply" in group and "button-clear" not in group


@pytest.mark.django_db
def test_search_hint_does_not_sit_inside_the_row_height(parking: dict[str, Branch]) -> None:
    content = _get()

    assert 'class="field field-search"' in content
    assert 'class="field-hint field-hint-below"' in content


@pytest.mark.django_db
def test_search_value_is_escaped(parking: dict[str, Branch]) -> None:
    content = _get("?search=%22%3E%3Cscript%3Ealert(1)%3C/script%3E")

    assert '"><script>' not in content
    assert "&quot;&gt;&lt;script&gt;" in content


@pytest.mark.django_db
def test_export_follows_the_search(parking: dict[str, Branch]) -> None:
    response = Client().get("/reviews/export/?search=parking%20full")
    body = b"".join(response.streaming_content).decode("utf-8")  # type: ignore[attr-defined]

    assert "Parking was full" in body
    assert "No parking nearby" not in body
    assert len(body.splitlines()) == 2
    assert 'href="/reviews/export/?search=parking"' in _get("?search=parking")


@pytest.mark.django_db
def test_the_search_term_is_never_logged(
    parking: dict[str, Branch], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        _get("?search=0909123456")
        Client().get("/reviews/export/?search=0909123456")

    assert "0909123456" not in caplog.text


@pytest.mark.django_db
def test_page_query_count_with_search_and_filters_over_many_branches(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    business = Business.objects.create(name="Demo")
    for index in range(20):
        branch = Branch.objects.create(business=business, name=f"Branch {index}")
        for number in range(3):
            _add(branch, 4, f"Parking is hard {number}", minutes=number)

    with django_assert_max_num_queries(3):
        _get("?search=parking%20hard&location=1&rating=good&week=2026-10-14")


@pytest.mark.django_db
def test_dashboard_and_api_ignore_the_search(parking: dict[str, Branch]) -> None:
    client = Client()

    assert client.get("/dashboard/?search=x").content == client.get("/dashboard/").content
    assert client.get("/api/dashboard/?search=x").json() == client.get("/api/dashboard/").json()
