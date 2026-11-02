from datetime import UTC, datetime

import pytest
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client
from django.urls import URLPattern, URLResolver, reverse
from pytest_django.fixtures import DjangoAssertNumQueries, Settings

from reviewradar import urls
from reviews.models import Branch, Business, Review

pytestmark = pytest.mark.login

PASSWORD = "correct-horse-battery"
PUBLIC_PAGES = {"login", "healthz"}
CLOSED_PATHS = ["/", "/dashboard/", "/reviews/", "/reviews/export/", "/api/dashboard/"]


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="anna", password=PASSWORD)


@pytest.fixture
def signed_in(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


def test_login_required_middleware_comes_right_after_authentication() -> None:
    middleware = django_settings.MIDDLEWARE
    position = middleware.index("django.contrib.auth.middleware.AuthenticationMiddleware")
    assert middleware[position + 1] == "django.contrib.auth.middleware.LoginRequiredMiddleware"


@pytest.mark.django_db
@pytest.mark.parametrize("path", CLOSED_PATHS)
def test_visitor_is_sent_to_sign_in_with_next(path: str) -> None:
    response = Client().get(path)

    assert response.status_code == 302
    assert response["Location"] == f"/login/?next={path}"


@pytest.mark.django_db
def test_visitor_keeps_the_review_list_query_string_in_next() -> None:
    response = Client().get("/reviews/?rating=5&page=2")

    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/reviews/%3Frating%3D5%26page%3D2"


@pytest.mark.django_db
def test_visitor_gets_no_data_from_export_or_api() -> None:
    business = Business.objects.create(name="Demo")
    Branch.objects.create(business=business, name="Secret branch")

    for path in ("/reviews/export/", "/api/dashboard/"):
        response = Client().get(path)
        assert response.status_code == 302
        assert b"Secret branch" not in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/login/", "/healthz/"])
def test_sign_in_page_and_health_path_stay_public(path: str) -> None:
    assert Client().get(path).status_code == 200


def test_static_files_are_served_without_signing_in(settings: Settings) -> None:
    settings.WHITENOISE_USE_FINDERS = True
    settings.WHITENOISE_AUTOREFRESH = True

    response = Client().get("/static/reviews/app.css")

    assert response.status_code == 200


@pytest.mark.django_db
def test_unknown_path_answers_the_not_found_page_without_signing_in() -> None:
    response = Client().get("/no-such-page/")

    assert response.status_code == 404
    assert "Page not found" in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "text"),
    [
        ("/dashboard/", "Downtown"),
        ("/reviews/", "Great staff"),
        ("/reviews/export/", "Great staff"),
        ("/api/dashboard/", "Downtown"),
    ],
)
def test_signed_in_user_gets_every_page(signed_in: Client, path: str, text: str) -> None:
    _add_branch(Business.objects.create(name="Demo"), "Downtown", (5,))

    response = signed_in.get(path)

    assert response.status_code == 200
    body = response.getvalue() if response.streaming else response.content
    assert text in body.decode()


def test_signed_in_user_is_sent_from_home_to_dashboard(signed_in: Client) -> None:
    response = signed_in.get("/")

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


@pytest.mark.django_db
@pytest.mark.parametrize("branch_count", [20, 200])
def test_signed_in_dashboard_needs_at_most_five_queries(
    signed_in: Client, branch_count: int, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    business = Business.objects.create(name="Demo")
    for index in range(branch_count):
        _add_branch(business, f"Branch {index}", (4, 5, 3))

    with django_assert_max_num_queries(5):
        response = signed_in.get("/dashboard/")

    assert response.status_code == 200
    assert f"Branch {branch_count - 1}" in response.content.decode()


@pytest.mark.django_db
def test_every_page_but_sign_in_and_health_needs_an_account() -> None:
    open_pages = []
    for name, path in _named_paths(urls.urlpatterns):
        if name in PUBLIC_PAGES:
            continue
        response = Client().get(path)
        if response.status_code != 302 or not response["Location"].startswith("/login/"):
            open_pages.append(name)

    assert open_pages == []


def _named_paths(patterns: list[URLPattern | URLResolver]) -> list[tuple[str, str]]:
    found = []
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            found += _named_paths(list(pattern.url_patterns))
        elif pattern.name and not pattern.pattern.regex.groups:
            found.append((pattern.name, reverse(pattern.name)))
    return found


def _add_branch(business: Business, name: str, ratings: tuple[int, ...]) -> Branch:
    branch = Branch.objects.create(business=business, name=name)
    for rating in ratings:
        Review.objects.create(
            branch=branch,
            rating=rating,
            text="Great staff",
            created_at=datetime(2026, 10, 20, 9, 0, tzinfo=UTC),
        )
    return branch
