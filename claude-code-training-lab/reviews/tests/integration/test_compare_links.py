import pytest
from django.core.management import call_command
from django.test import Client

from reviews.models import Branch

pytestmark = pytest.mark.django_db


@pytest.fixture
def demo() -> dict[str, int]:
    call_command("seed_demo_data")
    return {b.name: b.pk for b in Branch.objects.all()}


def _get(path: str) -> str:
    return Client().get(path).content.decode()


def test_sidebar_compare_sits_between_topics_and_reply_drafts(demo: dict[str, int]) -> None:
    html = _get("/topics/")
    assert html.index("Topics\n        </a>") < html.index("Compare\n") < html.index("Reply drafts")


def test_sidebar_compare_is_active_on_compare_page_only(demo: dict[str, int]) -> None:
    active = 'class="nav-item is-active" href="/compare/" aria-current="page"'
    assert active in _get("/compare/")
    other = _get("/reviews/")
    assert active not in other
    assert 'class="nav-item" href="/compare/"' in other


def test_location_page_links_to_compare_with_its_id(demo: dict[str, int]) -> None:
    pk = demo["Riverside"]
    html = _get(f"/locations/{pk}/")
    assert f'class="button" href="/compare/?a={pk}"' in html
    assert "Compare with another location" in html
    assert "Export JSON" not in html


def test_compare_page_shows_the_linked_location_as_a(demo: dict[str, int]) -> None:
    pk = demo["Riverside"]
    html = _get(f"/compare/?a={pk}")
    assert f'value="{pk}" selected' in html
