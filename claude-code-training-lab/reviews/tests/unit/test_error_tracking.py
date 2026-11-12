import tomllib
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.types import Event

PROJECT = Path(__file__).resolve().parents[3]
COMMIT = "5213e39b1c0f4a7d8e6a9b2c3d4e5f6071829304"


def test_pyproject_lists_sentry_sdk_django_dependency() -> None:
    data = tomllib.loads((PROJECT / "pyproject.toml").read_text())
    assert "sentry-sdk[django]>=2.40" in data["project"]["dependencies"]


def test_lock_file_has_sentry_sdk_package() -> None:
    data = tomllib.loads((PROJECT / "uv.lock").read_text())
    assert "sentry-sdk" in {package["name"] for package in data["package"]}


@pytest.mark.parametrize("env", [{}, {"SENTRY_DSN": ""}, {"SENTRY_DSN": "  "}])
def test_blank_dsn_does_nothing_and_returns_false(
    mocker: MockerFixture, env: dict[str, str]
) -> None:
    from reviewradar.monitoring import init_error_tracking

    init = mocker.patch("reviewradar.monitoring.sentry_sdk.init")

    assert init_error_tracking(env, False) is False
    init.assert_not_called()


def test_dsn_set_initialises_sentry_once_with_safe_options(mocker: MockerFixture) -> None:
    from reviewradar.monitoring import init_error_tracking, scrub_event

    init = mocker.patch("reviewradar.monitoring.sentry_sdk.init")
    env = {"SENTRY_DSN": "  https://key@example.ingest.sentry.io/1  ", "RENDER_GIT_COMMIT": COMMIT}

    assert init_error_tracking(env, False) is True

    init.assert_called_once()
    kwargs = init.call_args.kwargs
    assert init.call_args.args == ()
    assert kwargs["dsn"] == "https://key@example.ingest.sentry.io/1"
    assert len(kwargs["integrations"]) == 1
    assert isinstance(kwargs["integrations"][0], DjangoIntegration)
    assert kwargs["send_default_pii"] is False
    assert kwargs["include_local_variables"] is False
    assert kwargs["max_request_body_size"] == "never"
    assert kwargs["traces_sample_rate"] == 0.0
    assert kwargs["environment"] == "production"
    assert kwargs["release"] == COMMIT
    assert kwargs["before_send"] is scrub_event


def test_debug_uses_development_environment_and_blank_commit_gives_no_release(
    mocker: MockerFixture,
) -> None:
    from reviewradar.monitoring import init_error_tracking

    init = mocker.patch("reviewradar.monitoring.sentry_sdk.init")
    env = {"SENTRY_DSN": "https://key@example.ingest.sentry.io/1", "RENDER_GIT_COMMIT": " "}

    assert init_error_tracking(env, True) is True

    assert init.call_args.kwargs["environment"] == "development"
    assert init.call_args.kwargs["release"] is None


def test_scrub_event_keeps_only_url_of_request() -> None:
    from reviewradar.monitoring import scrub_event

    event: Event = {
        "message": "boom",
        "request": {
            "url": "https://example.com/reviews/",
            "query_string": "email=a@b.c",
            "data": {"text": "private"},
            "cookies": {"sessionid": "x"},
        },
    }

    result = scrub_event(event, {})

    assert result is not None
    assert result["request"] == {"url": "https://example.com/reviews/"}
    assert result["message"] == "boom"


def test_scrub_event_without_request_is_returned_unchanged() -> None:
    from reviewradar.monitoring import scrub_event

    event: Event = {"message": "boom"}

    assert scrub_event(event, {}) == {"message": "boom"}
