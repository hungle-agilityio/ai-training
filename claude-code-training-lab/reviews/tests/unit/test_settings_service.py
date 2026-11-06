import pytest
from pytest_django.fixtures import Settings

from reviews.settings_service import SuggestionStatus, suggestion_status

KEY = "sk-test-not-real"


def configure(settings: Settings, *, key: str, debug: bool, fake: bool = False) -> None:
    settings.ANTHROPIC_API_KEY = key
    settings.DEBUG = debug
    settings.REVIEWRADAR_AI_FAKE = fake
    settings.ANTHROPIC_MODEL = "claude-test-model"


def test_live_mode_is_on_with_the_model_name(settings: Settings) -> None:
    configure(settings, key=KEY, debug=False)
    status = suggestion_status()
    assert status.mode == "live"
    assert status.label == "On"
    assert status.detail == "Staff can ask Claude for a reply draft on each review's reply page."
    assert status.model == "claude-test-model"


def test_fake_mode_is_demo_without_a_model(settings: Settings) -> None:
    configure(settings, key="", debug=True)
    status = suggestion_status()
    assert status.mode == "fake"
    assert status.label == "Demo"
    assert status.detail == (
        "No API key: the button gives a fixed sample draft and nothing is sent to Claude."
    )
    assert status.model is None


def test_off_mode_is_off_without_a_model(settings: Settings) -> None:
    configure(settings, key="", debug=False)
    status = suggestion_status()
    assert status.mode == "off"
    assert status.label == "Off"
    assert status.detail == (
        'The "Suggest a reply" button is hidden. Your ReviewRadar admin can turn it on.'
    )
    assert status.model is None


def test_status_is_a_frozen_dataclass(settings: Settings) -> None:
    configure(settings, key="", debug=False)
    status = suggestion_status()
    assert isinstance(status, SuggestionStatus)
    with pytest.raises(AttributeError):
        status.label = "x"  # type: ignore[misc]


def test_status_makes_no_database_query(settings: Settings) -> None:
    configure(settings, key=KEY, debug=False)
    suggestion_status()  # no `db` fixture: a query would raise
