import importlib
from types import ModuleType

import pytest
from django.test import Client

import reviewradar.settings as project_settings

LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
RENDER_HOST = "reviewradar-zo3u.onrender.com"
ENV_NAMES = (
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_DEBUG",
    "DJANGO_SECRET_KEY",
    "RENDER_EXTERNAL_HOSTNAME",
)


@pytest.fixture
def load_settings(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Reload the settings module with the given environment, then restore it."""

    def _load(**env: str | None) -> ModuleType:
        for name in ENV_NAMES:
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            if value is not None:
                monkeypatch.setenv(name, value)
        return importlib.reload(project_settings)

    yield _load
    monkeypatch.undo()
    importlib.reload(project_settings)


def test_render_host_is_added_to_allowed_hosts_and_csrf_origins(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(RENDER_EXTERNAL_HOSTNAME=f"  {RENDER_HOST} ")

    assert settings.ALLOWED_HOSTS == [*LOCAL_HOSTS, RENDER_HOST]
    assert settings.CSRF_TRUSTED_ORIGINS == [f"https://{RENDER_HOST}"]


def test_render_host_comes_after_the_listed_hosts(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(
        DJANGO_ALLOWED_HOSTS="a.example.com", RENDER_EXTERNAL_HOSTNAME=RENDER_HOST
    )

    assert settings.ALLOWED_HOSTS == [*LOCAL_HOSTS, "a.example.com", RENDER_HOST]
    assert settings.CSRF_TRUSTED_ORIGINS == ["https://a.example.com", f"https://{RENDER_HOST}"]


def test_render_host_already_listed_is_not_repeated(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(
        DJANGO_ALLOWED_HOSTS=f"a.example.com,{RENDER_HOST}", RENDER_EXTERNAL_HOSTNAME=RENDER_HOST
    )

    assert settings.ALLOWED_HOSTS == [*LOCAL_HOSTS, "a.example.com", RENDER_HOST]
    assert settings.CSRF_TRUSTED_ORIGINS == ["https://a.example.com", f"https://{RENDER_HOST}"]


@pytest.mark.parametrize("value", [None, "", "   "])
def test_unset_or_blank_render_host_changes_nothing(load_settings, value: str | None) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(DJANGO_ALLOWED_HOSTS="a.example.com", RENDER_EXTERNAL_HOSTNAME=value)

    assert settings.ALLOWED_HOSTS == [*LOCAL_HOSTS, "a.example.com"]
    assert settings.CSRF_TRUSTED_ORIGINS == ["https://a.example.com"]


@pytest.mark.django_db
def test_dashboard_answers_200_on_the_render_host_with_debug_off(  # type: ignore[no-untyped-def]
    load_settings, settings, client: Client
) -> None:
    loaded = load_settings(
        DJANGO_DEBUG="0", DJANGO_SECRET_KEY="a-real-key", RENDER_EXTERNAL_HOSTNAME=RENDER_HOST
    )
    settings.ALLOWED_HOSTS = loaded.ALLOWED_HOSTS

    response = client.get("/dashboard/", HTTP_HOST=RENDER_HOST)

    assert response.status_code == 200
