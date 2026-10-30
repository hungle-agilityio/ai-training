import re

from django.conf import LazySettings
from django.test import Client

from reviewradar import settings as project_settings


def _get_missing_page(settings: LazySettings) -> tuple[int, str]:
    settings.DEBUG = False
    response = Client().get("/no-such-page/")
    return response.status_code, response.content.decode()


def test_missing_address_returns_404_in_app_layout(settings: LazySettings) -> None:
    status, html = _get_missing_page(settings)

    assert status == 404
    assert 'aria-label="Main navigation"' in html
    assert "Dashboard" in html and "Reviews" in html
    assert "ReviewRadar &middot; Know what your customers say, branch by branch." in html or (
        "ReviewRadar · Know what your customers say, branch by branch." in html
    )


def test_page_shows_texts_in_order_and_title(settings: LazySettings) -> None:
    _, html = _get_missing_page(settings)

    assert "<title>Page not found · ReviewRadar</title>" in html
    positions = [html.index(t) for t in (">404<", ">Page not found<", "This page may have moved")]
    assert positions == sorted(positions)
    assert "This page may have moved, or the link may be wrong." in html
    assert "We couldn't find that page." not in html


def test_page_not_found_is_the_only_non_empty_h1(settings: LazySettings) -> None:
    _, html = _get_missing_page(settings)

    headings = [h.strip() for h in re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S)]
    assert [h for h in headings if h] == ["Page not found"]


def test_404_number_is_hidden_from_screen_readers(settings: LazySettings) -> None:
    _, html = _get_missing_page(settings)

    assert re.search(r'<[^>]*aria-hidden="true"[^>]*>\s*404\s*<', html)


def test_only_back_to_dashboard_is_the_main_button(settings: LazySettings) -> None:
    _, html = _get_missing_page(settings)

    back = re.search(r'<a([^>]*)>\s*Back to Dashboard\s*</a>', html)
    reviews = re.search(r'<a([^>]*)>\s*View all reviews\s*</a>', html)
    assert back is not None and reviews is not None
    assert 'href="/dashboard/"' in back.group(1)
    assert 'href="/reviews/"' in reviews.group(1)
    assert "not-found-primary" in back.group(1)
    assert "not-found-primary" not in reviews.group(1)
    assert "button" in reviews.group(1)


def test_page_has_no_export_button_and_no_active_nav_item(settings: LazySettings) -> None:
    _, html = _get_missing_page(settings)

    assert "Export JSON" not in html
    assert "is-active" not in html.split("</aside>")[0].replace(".is-active", "")
    assert 'aria-current="page"' not in html


def test_allowed_hosts_are_only_the_local_ones() -> None:
    assert project_settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1", "[::1]"]
