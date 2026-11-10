from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, ReplyTemplate, Review, ReviewReply

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


@pytest.fixture
def review(branch: Branch) -> Review:
    return Review.objects.create(
        branch=branch, rating=2, text="Waited an hour.", created_at=NOW - timedelta(days=2)
    )


def url(review: Review) -> str:
    return f"/reviews/{review.id}/reply/"


def make(name: str, kind: str, text: str = "Sorry, {location} will call you.") -> ReplyTemplate:
    return ReplyTemplate.objects.create(name=name, kind=kind, text=text)


def test_page_lists_only_fitting_templates_by_name_ignoring_case(review: Review) -> None:
    make("beta", "bad")
    make("Alpha", "any")
    make("Zed good", "good")
    page = Client().get(url(review)).content.decode()
    assert 'id="reply-template"' in page
    assert 'class="reply-template"' in page
    assert "Zed good" not in page
    assert page.index("Alpha") < page.index("beta")
    assert 'name="action" value="template"' in page
    assert "formnovalidate" in page


def test_no_fitting_templates_shows_empty_note_and_link(review: Review) -> None:
    make("Only good", "good")
    page = Client().get(url(review)).content.decode()
    assert "No reply templates yet. Add them in" in page
    assert ">Settings</a>." in page
    assert "/settings/#settings-templates" in page
    assert 'value="template"' not in page


def test_use_template_fills_box_with_location_and_saves_nothing(review: Review) -> None:
    template = make("Apology", "bad")
    response = Client().post(
        url(review), {"action": "template", "template": template.id, "text": "old"}
    )
    page = response.content.decode()
    assert response.status_code == 200
    assert "Sorry, Clinic A will call you." in page
    assert "old</textarea>" not in page
    assert "Template filled in. Edit it before you save." in page
    assert 'role="status"' in page
    assert not ReviewReply.objects.exists()


@pytest.mark.parametrize("value", ["999", "abc", ""])
def test_unknown_template_keeps_typed_text(review: Review, value: str) -> None:
    make("Apology", "bad")
    page = (
        Client()
        .post(url(review), {"action": "template", "template": value, "text": "my words"})
        .content.decode()
    )
    assert "my words</textarea>" in page
    assert "Choose a template from the list." in page
    assert "Template filled in" not in page


def test_template_of_other_kind_is_refused(review: Review) -> None:
    other = make("Happy", "good")
    page = (
        Client()
        .post(url(review), {"action": "template", "template": other.id, "text": "mine"})
        .content.decode()
    )
    assert "mine</textarea>" in page
    assert "Choose a template from the list." in page


def test_save_reply_still_works(review: Review) -> None:
    make("Apology", "bad")
    response = Client().post(url(review), {"text": "Thanks."})
    assert response.status_code == 302
    assert ReviewReply.objects.get(review=review).text == "Thanks."


def test_get_makes_at_most_two_queries(
    review: Review, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    make("Apology", "bad")
    with django_assert_max_num_queries(2):
        Client().get(url(review))


def test_use_template_makes_at_most_three_queries(
    review: Review, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    template = make("Apology", "bad")
    with django_assert_max_num_queries(3):
        Client().post(url(review), {"action": "template", "template": template.id, "text": ""})
