import importlib
from collections.abc import Callable, Iterator
from types import ModuleType

import pytest
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

import reviewradar.settings as project_settings

PASSWORD = "correct-horse-battery"


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="demo", password=PASSWORD)


def test_settings_enable_sessions_and_auth_middleware_in_order() -> None:
    assert "django.contrib.sessions" in django_settings.INSTALLED_APPS
    middleware = django_settings.MIDDLEWARE
    assert middleware[0] == "django.middleware.security.SecurityMiddleware"
    assert middleware[1] == "whitenoise.middleware.WhiteNoiseMiddleware"
    ordered = [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
    ]
    positions = [middleware.index(name) for name in ordered]
    assert positions == sorted(positions)


def test_settings_hold_default_password_validators_and_redirects() -> None:
    names = [v["NAME"].rsplit(".", 1)[1] for v in django_settings.AUTH_PASSWORD_VALIDATORS]
    assert names == [
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    ]
    assert django_settings.LOGIN_URL == "login"
    assert django_settings.LOGIN_REDIRECT_URL == "dashboard"
    assert django_settings.LOGOUT_REDIRECT_URL == "login"


def test_login_page_shows_the_design_texts(db: None) -> None:
    response = Client().get("/login/")
    html = response.content.decode()

    assert response.status_code == 200
    assert 'aria-label="Main navigation"' not in html
    assert "ReviewRadar" in html
    assert ">Sign in</h1>" in html
    assert "Use the account your ReviewRadar admin gave you." in html
    assert "Username" in html and "Password" in html
    assert "Forgot your password? Ask your ReviewRadar admin to reset it." in html
    assert "csrfmiddlewaretoken" in html
    assert "reviews/app.css" in html


def test_right_password_redirects_to_dashboard(user: User) -> None:
    response = Client().post("/login/", {"username": "demo", "password": PASSWORD})

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


def test_right_password_follows_a_local_next_path(user: User) -> None:
    response = Client().post(
        "/login/?next=/reviews/", {"username": "demo", "password": PASSWORD, "next": "/reviews/"}
    )

    assert response.status_code == 302
    assert response["Location"] == "/reviews/"


def test_next_to_another_site_is_ignored(user: User) -> None:
    response = Client().post(
        "/login/",
        {"username": "demo", "password": PASSWORD, "next": "https://evil.example/steal"},
    )

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


def test_wrong_password_shows_django_message_and_keeps_username(user: User) -> None:
    response = Client().post("/login/", {"username": "demo", "password": "nope"})
    html = response.content.decode()

    assert response.status_code == 200
    assert "Please enter a correct username and password." in html
    assert "Note that both fields may be case-sensitive." in html
    assert 'value="demo"' in html
    assert "nope" not in html


def test_empty_fields_are_required(db: None) -> None:
    response = Client().post("/login/", {"username": "", "password": ""})

    assert response.status_code == 200
    assert response.content.decode().count("This field is required.") == 2


def test_signed_in_user_opening_login_goes_to_dashboard(user: User) -> None:
    client = Client()
    client.force_login(user)

    response = client.get("/login/")

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


def test_post_logout_signs_out_and_redirects_to_login(user: User) -> None:
    client = Client()
    client.force_login(user)

    response = client.post("/logout/")

    assert response.status_code == 302
    assert response["Location"] == "/login/"
    assert "_auth_user_id" not in client.session


def test_get_logout_is_not_allowed_and_keeps_session(user: User) -> None:
    client = Client()
    client.force_login(user)

    response = client.get("/logout/")

    assert response.status_code == 405
    assert "_auth_user_id" in client.session


def test_healthz_answers_ok_without_a_database_query(db: None) -> None:
    with CaptureQueriesContext(connection) as queries:
        response = Client().get("/healthz/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert len(queries) == 0


def test_healthz_is_marked_login_not_required() -> None:
    from reviews import views

    assert getattr(views.healthz, "login_required", None) is False


@pytest.fixture
def load_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[..., ModuleType]]:
    """Reload the settings module with the given environment, then restore it."""

    def _load(**env: str) -> ModuleType:
        for name in ("DJANGO_ALLOWED_HOSTS", "DJANGO_DEBUG", "DJANGO_SECRET_KEY"):
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(project_settings)

    yield _load
    monkeypatch.undo()
    importlib.reload(project_settings)


def test_cookies_are_secure_only_when_debug_is_off(
    load_settings: Callable[..., ModuleType],
) -> None:
    on = load_settings(DJANGO_DEBUG="0", DJANGO_SECRET_KEY="a-real-key")
    assert on.SESSION_COOKIE_SECURE is True
    assert on.CSRF_COOKIE_SECURE is True

    off = load_settings()
    assert off.SESSION_COOKIE_SECURE is False
    assert off.CSRF_COOKIE_SECURE is False
