import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client

PASSWORD = "correct-horse-battery"


@pytest.fixture
def signed_in(db: None) -> Client:
    user: User = get_user_model().objects.create_user(username="anna", password=PASSWORD)
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.parametrize("path", ["/dashboard/", "/reviews/"])
def test_signed_in_sidebar_shows_the_account_block(signed_in: Client, path: str) -> None:
    html = signed_in.get(path).content.decode()

    sidebar = html.split('aria-label="Main navigation"', 1)[1].split("</aside>", 1)[0]
    assert re.search(r"Signed in as\s*<strong data-sensitive>anna</strong>", sidebar)
    form = re.search(r'<form[^>]*class="account-signout"[^>]*>(.*?)</form>', sidebar, re.S)
    assert form is not None
    assert 'method="post"' in form.group(0)
    assert 'action="/logout/"' in form.group(0)
    assert 'name="csrfmiddlewaretoken"' in form.group(1)
    assert re.search(r"<button[^>]*>\s*Sign out\s*</button>", form.group(1))


def test_sign_out_button_signs_out(signed_in: Client) -> None:
    response = signed_in.post("/logout/")

    assert response.status_code == 302
    assert response["Location"] == "/login/"
    assert "_auth_user_id" not in signed_in.session


@pytest.mark.django_db
def test_not_found_page_without_sign_in_has_no_account_block() -> None:
    response = Client().get("/no-such-page/")
    html = response.content.decode()

    assert response.status_code == 404
    assert "Page not found" in html
    assert "Signed in as" not in html
    assert "Sign out" not in html
