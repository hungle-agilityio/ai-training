import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import ReplyTemplate

pytestmark = pytest.mark.login

URL = "/settings/templates/"


@pytest.fixture
def client(db: None) -> Client:
    user = get_user_model().objects.create_user(username="demo", password="correct-horse-battery")
    client = Client()
    client.force_login(user)
    return client


def make(name: str, kind: str = "any", text: str = "Thanks!") -> ReplyTemplate:
    return ReplyTemplate.objects.create(name=name, kind=kind, text=text)


def test_panel_sits_between_goals_and_suggestions_with_help_text(client: Client) -> None:
    html = client.get("/settings/").content.decode()
    assert '<section class="panel settings-panel" id="settings-templates">' in html
    assert html.index('id="settings-goals"') < html.index('id="settings-templates"')
    assert html.index('id="settings-templates"') < html.index('id="settings-suggestions"')
    assert "Reply templates" in html
    assert "Use {location} for the location's name." in html


def test_empty_panel_says_no_templates(client: Client) -> None:
    assert "No reply templates yet." in client.get("/settings/").content.decode()


def test_rows_are_ordered_ignoring_case_with_kind_label_and_edit_link(client: Client) -> None:
    bad = make("beta", "bad")
    good = make("Alpha", "good")
    anyone = make("gamma", "any")
    html = client.get("/settings/").content.decode()
    assert html.index("Alpha") < html.index("beta") < html.index("gamma")
    assert "Good review (4–5 ★)" in html
    assert "Bad review (1–2 ★)" in html
    assert "Any review" in html
    for template in (good, bad, anyone):
        assert f'href="/settings/templates/{template.id}/"' in html
    assert "No reply templates yet." not in html


def test_form_fields(client: Client) -> None:
    html = client.get("/settings/").content.decode()
    assert 'action="/settings/templates/"' in html
    assert 'maxlength="60"' in html
    assert 'maxlength="1000"' in html
    assert html.index('value="any"') < html.index('value="good"') < html.index('value="bad"')
    assert "Add a template" in html
    assert "Add template" in html


def test_get_redirects_to_settings(client: Client) -> None:
    response = client.get(URL)
    assert response.status_code == 302
    assert response["Location"] == "/settings/"


def test_valid_post_creates_stripped_template_and_redirects(client: Client) -> None:
    response = client.post(URL, {"name": "  Thanks  ", "kind": "good", "text": "  Hi {location}  "})
    assert response.status_code == 302
    assert response["Location"] == "/settings/?templates=added#settings-templates"
    template = ReplyTemplate.objects.get()
    assert (template.name, template.kind, template.text) == ("Thanks", "good", "Hi {location}")
    html = client.get("/settings/?templates=added").content.decode()
    assert 'id="templates-saved"' in html
    assert 'role="status"' in html
    assert "Template added." in html


def test_no_notice_without_the_flag(client: Client) -> None:
    assert "Template added." not in client.get("/settings/").content.decode()


def test_invalid_post_saves_nothing_and_keeps_values(client: Client) -> None:
    response = client.post(URL, {"name": "", "kind": "bad", "text": "Sorry {oops}"})
    html = response.content.decode()
    assert response.status_code == 200
    assert ReplyTemplate.objects.count() == 0
    assert "Enter a name of 1 to 60 characters." in html
    assert "Unknown placeholder {oops}." in html
    assert "Sorry {oops}" in html
    assert 'aria-describedby="template-name-error"' in html
    assert 'aria-describedby="template-text-error"' in html
    assert 'id="settings-goals"' in html
    assert 'id="settings-account"' in html


def test_unknown_kind_is_refused(client: Client) -> None:
    response = client.post(URL, {"name": "x", "kind": "weird", "text": "ok"})
    assert response.status_code == 200
    assert ReplyTemplate.objects.count() == 0
    assert 'aria-describedby="template-kind-error"' in response.content.decode()


def test_duplicate_name_is_refused_ignoring_case(client: Client) -> None:
    make("Thanks")
    response = client.post(URL, {"name": "thanks", "kind": "any", "text": "ok"})
    assert "A template with this name already exists." in response.content.decode()
    assert ReplyTemplate.objects.count() == 1


def test_visitor_is_sent_to_sign_in(db: None) -> None:
    response = Client().post(URL, {"name": "x", "kind": "any", "text": "y"})
    assert response.status_code == 302
    assert response["Location"].startswith("/login/")
    assert ReplyTemplate.objects.count() == 0


def test_settings_query_count_does_not_grow_with_templates(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for number in range(6):
        make(f"t{number}")
    with django_assert_max_num_queries(4):
        assert client.get("/settings/").status_code == 200
