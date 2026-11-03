"""Every page names a ReviewRadar tab icon that exists, so no browser asks for a missing one."""

import pytest
from django.conf import LazySettings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client

from reviews.models import Branch, Business

ICON_PATH = "reviews/icon.svg"
ICON_LINK = '<link rel="icon" href="/static/reviews/icon.svg" type="image/svg+xml">'


@pytest.fixture
def signed_in(db: None) -> Client:
    client = Client()
    client.force_login(get_user_model().objects.create_user(username="anna", password="x-pass-1"))
    return client


def test_sign_in_page_names_the_tab_icon(db: None) -> None:
    html = Client().get("/login/").content.decode()
    assert ICON_LINK in html


@pytest.mark.parametrize("path", ["/dashboard/", "/reviews/"])
def test_app_pages_name_the_tab_icon(signed_in: Client, path: str) -> None:
    response = signed_in.get(path)
    assert response.status_code == 200
    assert ICON_LINK in response.content.decode()


def test_location_page_names_the_tab_icon(signed_in: Client) -> None:
    business = Business.objects.create(name="Demo")
    branch = Branch.objects.create(business=business, name="Airport")
    response = signed_in.get(f"/locations/{branch.pk}/")
    assert response.status_code == 200
    assert ICON_LINK in response.content.decode()


def test_not_found_page_names_the_tab_icon(settings: LazySettings, db: None) -> None:
    settings.DEBUG = False
    response = Client().get("/no-such-page/")
    assert response.status_code == 404
    assert ICON_LINK in response.content.decode()


def test_the_named_icon_is_a_static_svg_file() -> None:
    found = finders.find(ICON_PATH)
    assert isinstance(found, str), f"{ICON_PATH} is not in any static folder"
    with open(found, encoding="utf-8") as icon:
        text = icon.read()
    assert text.lstrip().startswith("<svg") and text.rstrip().endswith("</svg>")
    assert 'xmlns="http://www.w3.org/2000/svg"' in text
