from datetime import UTC, datetime

import pytest
from django.core.management import call_command
from django.template import Context, Template
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews.models import Branch, Business
from reviews.repositories import create_review
from reviews.templatetags.topic_tags import review_topics
from reviews.topics import Topic

NOW = datetime(2026, 10, 14, 5, 0, tzinfo=UTC)
LABEL = '<span class="badge badge-neutral topic-label">'


def _seed(*texts: str) -> None:
    branch = Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")
    for text in texts:
        create_review(branch=branch, rating=1, text=text, created_at=NOW)


def _get(query: str = "") -> str:
    return Client().get(f"/reviews/{query}").content.decode()


def test_filter_returns_topics_in_topic_order() -> None:
    result = review_topics("Front desk understaffed, queue out the door.")

    assert [topic.slug for topic in result] == ["wait", "staff"]
    assert review_topics("Best clinic experience I've had.") == ()


@pytest.mark.django_db
def test_row_shows_labels_after_sentiment_badge_in_topic_order() -> None:
    _seed("Front desk understaffed, queue out the door.")
    content = _get()
    row = content[content.index('class="review-row"') :]

    assert row.index("badge-negative") < row.index(">Wait time<")
    assert row.index(">Wait time<") < row.index(">Staff<")
    assert content.count(LABEL) == 2


@pytest.mark.django_db
def test_review_with_no_topic_shows_no_label() -> None:
    _seed("Best clinic experience I've had.")

    assert LABEL not in _get()


@pytest.mark.django_db
def test_labels_are_outside_the_sensitive_text_cell() -> None:
    _seed("Long queue today.")
    content = _get()
    cell_start = content.index('data-sensitive="review-text"')
    cell_end = content.index("</td>", cell_start)

    assert LABEL not in content[cell_start:cell_end]
    assert content.index(LABEL) > cell_end


def test_topic_label_is_escaped(mocker: MockerFixture) -> None:
    evil = Topic("wait", "<script>alert(1)</script>", ("queue",))
    mocker.patch("reviews.templatetags.topic_tags.topics_of", return_value=(evil,))
    html = Template(
        "{% load topic_tags %}{% for t in text|review_topics %}{{ t.label }}{% endfor %}"
    ).render(Context({"text": "queue"}))

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.django_db
def test_demo_page_has_labels_within_three_queries(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    call_command("seed_demo_data")
    with django_assert_max_num_queries(3):
        content = _get()

    assert LABEL in content
