from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, ReplyTemplate, Review, ReviewReply

pytestmark = pytest.mark.login

NOW = datetime(2026, 11, 1, tzinfo=UTC)


@pytest.fixture
def client(db: None) -> Client:
    user = get_user_model().objects.create_user(username="demo", password="correct-horse-battery")
    client = Client()
    client.force_login(user)
    return client


def make(name: str = "Thanks", kind: str = "good", text: str = "Hi {location}") -> ReplyTemplate:
    return ReplyTemplate.objects.create(name=name, kind=kind, text=text)


def edit_url(template: ReplyTemplate) -> str:
    return f"/settings/templates/{template.id}/"


def delete_url(template: ReplyTemplate) -> str:
    return f"/settings/templates/{template.id}/delete/"


def test_edit_page_shows_filled_form_and_links(client: Client) -> None:
    template = make()
    html = client.get(edit_url(template)).content.decode()
    assert "Edit reply template" in html
    assert 'value="Thanks"' in html
    assert ">Hi {location}</textarea>" in html
    assert '<option value="good" selected>' in html
    assert "Save template" in html
    assert 'href="/settings/#settings-templates"' in html
    assert "Cancel" in html
    assert f'href="/settings/templates/{template.id}/delete/"' in html
    assert "Delete template" in html


def test_edit_unknown_id_is_404(client: Client) -> None:
    assert client.get("/settings/templates/999/").status_code == 404
    data = {"name": "a", "kind": "any", "text": "b"}
    assert client.post("/settings/templates/999/", data).status_code == 404


def test_valid_post_saves_and_redirects_with_notice(client: Client) -> None:
    template = make()
    data = {"name": " Thanks ", "kind": "bad", "text": "  Sorry  "}
    response = client.post(edit_url(template), data)
    assert response.status_code == 302
    assert response["Location"] == "/settings/?templates=saved#settings-templates"
    template.refresh_from_db()
    assert (template.name, template.kind, template.text) == ("Thanks", "bad", "Sorry")
    html = client.get("/settings/?templates=saved").content.decode()
    assert 'id="templates-saved"' in html
    assert "Template saved." in html
    assert "Template added." not in html


def test_own_name_does_not_count_as_taken(client: Client) -> None:
    template = make("Thanks")
    response = client.post(edit_url(template), {"name": "THANKS", "kind": "any", "text": "ok"})
    assert response.status_code == 302


def test_other_name_is_taken(client: Client) -> None:
    make("Other")
    template = make("Thanks")
    response = client.post(edit_url(template), {"name": "other", "kind": "any", "text": "ok"})
    html = response.content.decode()
    assert response.status_code == 200
    assert "A template with this name already exists." in html
    assert 'aria-describedby="template-name-error"' in html


def test_invalid_post_shows_edit_page_with_typed_values(client: Client) -> None:
    template = make()
    data = {"name": "", "kind": "bad", "text": "Sorry {oops}"}
    response = client.post(edit_url(template), data)
    html = response.content.decode()
    assert response.status_code == 200
    assert "Edit reply template" in html
    assert "Enter a name of 1 to 60 characters." in html
    assert "Unknown placeholder {oops}." in html
    assert "Sorry {oops}" in html
    assert 'aria-describedby="template-name-error"' in html
    assert 'aria-describedby="template-text-error"' in html
    template.refresh_from_db()
    assert template.name == "Thanks"


def test_delete_page_asks_first(client: Client) -> None:
    template = make()
    html = client.get(delete_url(template)).content.decode()
    assert 'Delete the template "Thanks"? Saved replies do not change.' in html
    assert 'method="post"' in html
    assert "Delete template" in html
    assert f'href="/settings/templates/{template.id}/"' in html
    assert "Cancel" in html
    assert ReplyTemplate.objects.count() == 1


def test_delete_post_removes_template_and_keeps_saved_replies(client: Client) -> None:
    template = make()
    branch = Branch.objects.create(business=Business.objects.create(name="B"), name="Main")
    review = Review.objects.create(branch=branch, rating=5, text="Great", created_at=NOW)
    ReviewReply.objects.create(review=review, text="Thank you!", created_at=NOW, updated_at=NOW)
    response = client.post(delete_url(template))
    assert response.status_code == 302
    assert response["Location"] == "/settings/?templates=deleted#settings-templates"
    assert ReplyTemplate.objects.count() == 0
    assert ReviewReply.objects.get().text == "Thank you!"
    html = client.get("/settings/?templates=deleted").content.decode()
    assert 'id="templates-saved"' in html
    assert "Template deleted." in html


def test_delete_unknown_id_is_404(client: Client) -> None:
    assert client.get("/settings/templates/999/delete/").status_code == 404
    assert client.post("/settings/templates/999/delete/").status_code == 404


def test_signed_out_visitor_is_sent_to_sign_in(db: None) -> None:
    template = make()
    for url in (edit_url(template), delete_url(template)):
        response = Client().get(url)
        assert response.status_code == 302
        assert response["Location"].startswith("/login/")


def test_pages_run_at_most_three_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    template = make()
    with django_assert_max_num_queries(3):
        client.get(edit_url(template))
    with django_assert_max_num_queries(3):
        client.get(delete_url(template))
