import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries, Settings

pytestmark = pytest.mark.login

KEY = "sk-test-not-real"


@pytest.fixture
def client(db: None) -> Client:
    user: User = get_user_model().objects.create_user(username="demo", password="pw-correct-horse")
    client = Client()
    client.force_login(user)
    return client


def page(client: Client, settings: Settings, *, key: str, debug: bool) -> str:
    settings.ANTHROPIC_API_KEY = key
    settings.DEBUG = debug
    settings.REVIEWRADAR_AI_FAKE = False
    settings.ANTHROPIC_MODEL = "claude-test-model"
    return client.get("/settings/").content.decode()


def test_live_panel_shows_on_badge_and_model(client: Client, settings: Settings) -> None:
    html = page(client, settings, key=KEY, debug=False)
    assert 'id="settings-suggestions"' in html
    assert "Reply suggestions" in html
    assert "badge-positive" in html
    assert ">On<" in html
    assert "Model: claude-test-model" in html
    assert KEY not in html


def test_demo_panel_shows_watch_badge_and_no_model(client: Client, settings: Settings) -> None:
    html = page(client, settings, key="", debug=True)
    assert "badge-watch" in html
    assert ">Demo<" in html
    assert "No API key: the button gives a fixed sample draft" in html
    assert "Model:" not in html


def test_off_panel_shows_neutral_badge_and_no_model(client: Client, settings: Settings) -> None:
    html = page(client, settings, key="", debug=False)
    assert "badge-neutral" in html
    assert ">Off<" in html
    assert "Your ReviewRadar admin can turn it on." in html
    assert "Model:" not in html


def test_panel_comes_after_the_account_panel(client: Client, settings: Settings) -> None:
    html = page(client, settings, key=KEY, debug=False)
    assert html.index('id="settings-account"') < html.index('id="settings-suggestions"')


def test_settings_page_makes_at_most_two_queries(
    client: Client,
    settings: Settings,
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    settings.ANTHROPIC_API_KEY = KEY
    with django_assert_max_num_queries(2):
        client.get("/settings/")
