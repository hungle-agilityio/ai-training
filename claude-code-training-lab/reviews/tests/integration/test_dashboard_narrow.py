"""The dashboard fits a phone screen: grid children may shrink, so only the table scrolls."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import Client

STYLE_PATH = "reviews/app.css"
SHRINK_RULE = ".grid > * { min-width: 0; }"


@pytest.fixture
def signed_in(db: None) -> Client:
    client = Client()
    client.force_login(get_user_model().objects.create_user(username="anna", password="x-pass-1"))
    return client


def test_grid_children_may_shrink_below_their_content() -> None:
    found = finders.find(STYLE_PATH)
    assert isinstance(found, str), f"{STYLE_PATH} is not in any static folder"
    with open(found, encoding="utf-8") as style:
        text = style.read()
    assert SHRINK_RULE in text


def test_dashboard_links_the_app_style_sheet(signed_in: Client) -> None:
    response = signed_in.get("/dashboard/")
    assert response.status_code == 200
    assert static(STYLE_PATH) in response.content.decode()
