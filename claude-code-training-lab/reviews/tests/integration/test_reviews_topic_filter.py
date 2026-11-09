from datetime import UTC, datetime
from html import escape

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business
from reviews.repositories import create_review
from reviews.services import (
    REVIEWS_PER_PAGE,
    ReviewFilters,
    ReviewSelection,
    resolve_selection,
)
from reviews.topics import TOPICS

NOW = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)


@pytest.fixture
def demo(db: None) -> None:
    call_command("seed_demo_data")


def _get(query: str = "") -> str:
    return Client().get(f"/reviews/{query}").content.decode()


def _export(query: str) -> list[str]:
    response = Client().get(f"/reviews/export/{query}")
    body = b"".join(response.streaming_content).decode("utf-8")  # type: ignore[attr-defined]
    return body.splitlines()


def test_topic_select_follows_rating_with_all_topics_and_seven_labels(demo: None) -> None:
    content = _get()

    assert 'id="filter-topic" name="topic"' in content
    assert '<label for="filter-topic">Topic</label>' in content
    assert content.index("filter-rating") < content.index("filter-topic")
    assert '<option value="" selected>All topics</option>' in content
    positions = [
        content.index(f'<option value="{t.slug}">{escape(t.label)}</option>') for t in TOPICS
    ]
    assert positions == sorted(positions)


def test_chosen_topic_is_selected(demo: None) -> None:
    content = _get("?topic=wait")

    assert '<option value="wait" selected>Wait time</option>' in content
    assert '<option value="" selected>All topics</option>' not in content


def test_demo_counts(demo: None) -> None:
    assert "4 reviews" in _get("?topic=wait")
    assert "2 reviews" in _get("?topic=wait&rating=bad")
    assert "14 reviews" in _get("?topic=nope")


def test_topic_combines_with_search_and_location(db: None) -> None:
    business = Business.objects.create(name="B")
    north = Branch.objects.create(business=business, name="North")
    south = Branch.objects.create(business=business, name="South")
    create_review(branch=north, rating=5, text="long wait, kind nurse", created_at=NOW)
    create_review(branch=south, rating=5, text="long wait", created_at=NOW)
    create_review(branch=north, rating=5, text="great place", created_at=NOW)

    assert "2 reviews" in _get("?topic=wait")
    assert "1 review<" in _get(f"?topic=wait&location={north.id}")
    assert "1 review<" in _get("?topic=wait&search=nurse")


def test_topic_is_kept_in_page_links_and_export_link(db: None) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="B"), name="N")
    for index in range(REVIEWS_PER_PAGE + 1):
        create_review(branch=branch, rating=1, text=f"long wait {index}", created_at=NOW)

    content = _get("?topic=wait&rating=bad")

    assert "?rating=bad&amp;topic=wait&amp;page=2" in content
    assert "/reviews/export/?rating=bad&amp;topic=wait" in content


def test_topic_is_appended_after_the_other_params() -> None:
    selection = resolve_selection(
        ReviewFilters(rating="bad", reply="no", topic="wait"), branch_ids=set()
    )

    assert selection.params == [("rating", "bad"), ("reply", "no"), ("topic", "wait")]
    assert selection.topic == "wait"


def test_unknown_topic_is_dropped_and_old_links_do_not_change() -> None:
    selection = resolve_selection(ReviewFilters(rating="bad", topic="nope"), branch_ids=set())

    assert selection.params == [("rating", "bad")]
    assert selection.topic is None
    assert ReviewFilters() == ReviewFilters(topic=None)
    assert ReviewSelection.__dataclass_fields__["topic"].default is None


def test_topic_counts_as_a_filter_for_clear_and_no_reviews_found(db: None) -> None:
    business = Business.objects.create(name="B")
    create_review(
        branch=Branch.objects.create(business=business, name="N"),
        rating=5,
        text="nice",
        created_at=NOW,
    )

    content = _get("?topic=wait")

    assert "No reviews found" in content
    assert "button-clear" in content


def test_export_csv_keeps_only_matching_reviews_and_the_file_name(demo: None) -> None:
    rows = _export("?topic=wait")
    assert len(rows) == 1 + 4

    response = Client().get("/reviews/export/?topic=wait")
    assert response["Content-Disposition"].startswith('attachment; filename="reviews-')
    assert "wait" not in response["Content-Disposition"]
    assert len(_export("?topic=wait&rating=bad")) == 1 + 2


def test_query_count_is_at_most_three_with_a_topic_and_many_locations(
    db: None, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="B")
    for index in range(20):
        branch = Branch.objects.create(business=business, name=f"L{index}")
        create_review(branch=branch, rating=2, text="long wait", created_at=NOW)

    with django_assert_max_num_queries(3):
        response = Client().get("/reviews/?topic=wait")

    assert response.status_code == 200
