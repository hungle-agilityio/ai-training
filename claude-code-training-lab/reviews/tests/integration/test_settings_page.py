import re
from typing import cast

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

pytestmark = pytest.mark.login

PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "a-brand-new-passphrase"


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="demo", password=PASSWORD)


@pytest.fixture
def client(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


def change(
    client: Client, old: str = PASSWORD, new1: str = NEW_PASSWORD, new2: str = ""
) -> HttpResponse:
    data = {"old_password": old, "new_password1": new1, "new_password2": new2 or new1}
    return cast(HttpResponse, client.post("/settings/", data))


def test_page_has_title_heading_subtitle_and_no_export_button(client: Client) -> None:
    response = client.get("/settings/")
    page = response.content.decode()
    assert response.status_code == 200
    assert "reviews/settings.html" in [t.name for t in response.templates]
    assert "<title>Settings · ReviewRadar</title>" in page
    assert "<h1>Settings</h1>" in page
    assert "Your account and how ReviewRadar is set up." in page
    assert "Export JSON" not in page


def test_visitor_is_sent_to_sign_in(db: None) -> None:
    response = Client().get("/settings/")
    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/settings/"


def test_sidebar_item_is_a_link_on_every_page_and_active_here(client: Client) -> None:
    page = client.get("/settings/").content.decode()
    assert 'class="nav-item is-active" href="/settings/" aria-current="page"' in page
    assert "<em>Soon</em>" not in page
    assert "is-disabled" not in page
    other = client.get("/reviews/").content.decode()
    assert '<a class="nav-item" href="/settings/">' in other
    assert "is-disabled" not in other


def test_account_panel_shows_username_read_only(client: Client) -> None:
    page = client.get("/settings/").content.decode()
    assert 'id="settings-account"' in page
    assert "<h2>Account</h2>" in page
    assert "Username" in page
    assert "<strong data-sensitive>demo</strong>" in page
    assert "To change your username, ask your ReviewRadar admin." in page


def test_password_form_fields_hint_and_button(client: Client) -> None:
    page = client.get("/settings/").content.decode()
    assert "<h3>Change password</h3>" in page
    assert 'method="post"' in page
    assert "csrfmiddlewaretoken" in page
    assert page.index("old_password") < page.index("new_password1") < page.index("new_password2")
    assert 'autocomplete="current-password"' in page
    assert page.count('autocomplete="new-password"') == 2
    for label in ("Current password", "New password", "Confirm new password"):
        assert label in page
    assert (
        "At least 8 characters, not only numbers, not a common password and not like your username."
    ) in page
    assert "Change password</button>" in page
    assert 'id="password-saved"' not in page


def test_valid_post_changes_password_and_keeps_session(client: Client, user: User) -> None:
    other = Client()
    other.force_login(user)
    response = change(client)
    assert response.status_code == 302
    assert response["Location"] == "/settings/?saved=1"
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert client.get("/settings/").status_code == 200
    assert other.get("/settings/").status_code == 302


def test_saved_flag_shows_message_only_for_one(client: Client) -> None:
    page = client.get("/settings/?saved=1").content.decode()
    assert 'id="password-saved"' in page
    assert 'role="status"' in page
    assert "Password changed." in page
    for value in ("0", "yes", ""):
        assert "password-saved" not in client.get("/settings/?saved=" + value).content.decode()


def test_wrong_current_password_is_refused(client: Client, user: User) -> None:
    response = change(client, old="nope")
    page = response.content.decode()
    assert response.status_code == 200
    assert "Your old password was entered incorrectly. Please enter it again." in page
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert NEW_PASSWORD not in page
    assert PASSWORD not in page


def test_different_new_passwords_are_refused(client: Client, user: User) -> None:
    page = change(client, new2="something-else-entirely").content.decode()
    assert "The two password fields didn’t match." in page
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_empty_post_shows_required_errors_and_described_by_ids_exist(client: Client) -> None:
    page = client.post("/settings/", {}).content.decode()
    assert page.count("This field is required.") == 3
    assert "autofocus" not in page
    for target in re.findall(r'aria-describedby="([^"]+)"', page):
        for element_id in target.split():
            assert 'id="' + element_id + '"' in page


def test_validator_message_is_shown(client: Client, user: User) -> None:
    page = change(client, new1="short1x", new2="short1x").content.decode()
    assert "This password is too short. It must contain at least 8 characters." in page
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_post_without_csrf_token_is_403(user: User) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    assert client.post("/settings/", {"old_password": PASSWORD}).status_code == 403


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_other_methods_are_405(client: Client, method: str) -> None:
    assert getattr(client, method)("/settings/").status_code == 405


def test_get_makes_at_most_two_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(4):
        assert client.get("/settings/").status_code == 200
