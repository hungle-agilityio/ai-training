import importlib
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client

import reviewradar.settings as project_settings

LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
DEV_KEY = "dev-only-insecure-key"


@pytest.fixture
def load_settings(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Reload the settings module with the given environment, then restore it."""

    def _load(**env: str | None) -> ModuleType:
        for name in ("DJANGO_ALLOWED_HOSTS", "DJANGO_DEBUG", "DJANGO_SECRET_KEY"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            if value is not None:
                monkeypatch.setenv(name, value)
        return importlib.reload(project_settings)

    yield _load
    monkeypatch.undo()
    importlib.reload(project_settings)


def test_allowed_hosts_are_local_when_variable_is_unset(load_settings) -> None:  # type: ignore[no-untyped-def]
    assert load_settings().ALLOWED_HOSTS == LOCAL_HOSTS


def test_allowed_hosts_add_listed_hosts_ignoring_spaces_and_empty_items(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(DJANGO_ALLOWED_HOSTS=" a.example.com, ,b.example.com,, ")

    assert settings.ALLOWED_HOSTS == [*LOCAL_HOSTS, "a.example.com", "b.example.com"]


def test_csrf_trusted_origins_follow_listed_hosts(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(DJANGO_ALLOWED_HOSTS="a.example.com, b.example.com")

    assert settings.CSRF_TRUSTED_ORIGINS == ["https://a.example.com", "https://b.example.com"]


def test_csrf_trusted_origins_empty_when_variable_is_unset(load_settings) -> None:  # type: ignore[no-untyped-def]
    assert load_settings().CSRF_TRUSTED_ORIGINS == []


@pytest.mark.parametrize("key", [None, "", DEV_KEY])
def test_debug_off_rejects_missing_empty_or_dev_secret_key(load_settings, key: str | None) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ImproperlyConfigured):
        load_settings(DJANGO_DEBUG="0", DJANGO_SECRET_KEY=key)


def test_debug_off_accepts_a_real_secret_key(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings(DJANGO_DEBUG="0", DJANGO_SECRET_KEY="a-real-key")

    assert settings.SECRET_KEY == "a-real-key"
    assert settings.DEBUG is False


def test_debug_on_keeps_the_dev_key(load_settings) -> None:  # type: ignore[no-untyped-def]
    settings = load_settings()

    assert settings.DEBUG is True
    assert settings.SECRET_KEY == DEV_KEY


def test_whitenoise_comes_right_after_security_middleware() -> None:
    middleware = project_settings.MIDDLEWARE

    assert middleware[0] == "django.middleware.security.SecurityMiddleware"
    assert middleware[1] == "whitenoise.middleware.WhiteNoiseMiddleware"


def test_static_root_is_staticfiles_under_base_dir() -> None:
    assert project_settings.STATIC_ROOT == project_settings.BASE_DIR / "staticfiles"


def test_proxy_ssl_header_trusts_forwarded_proto() -> None:
    assert project_settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/dashboard/", "/reviews/"])
def test_pages_ask_search_engines_not_to_index(client: Client, path: str) -> None:
    response = client.get(path)

    assert '<meta name="robots" content="noindex, nofollow">' in response.content.decode()


def test_wsgi_exposes_application() -> None:
    wsgi = importlib.import_module("reviewradar.wsgi")

    assert callable(wsgi.application)
