import pytest
from pytest_django.fixtures import Settings

LOGIN_REQUIRED_MIDDLEWARE = "django.contrib.auth.middleware.LoginRequiredMiddleware"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "login: run with the real sign-in check")


@pytest.fixture(autouse=True)
def login_check_off_unless_marked(request: pytest.FixtureRequest, settings: Settings) -> None:
    """Tests not marked `login` run without the sign-in check, as before the auth epic."""
    middleware = list(settings.MIDDLEWARE)
    if request.node.get_closest_marker("login") is None and LOGIN_REQUIRED_MIDDLEWARE in middleware:
        settings.MIDDLEWARE = [name for name in middleware if name != LOGIN_REQUIRED_MIDDLEWARE]
