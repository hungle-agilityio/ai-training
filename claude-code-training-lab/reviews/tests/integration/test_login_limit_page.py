from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries
from pytest_mock import MockerFixture

from reviews import login_limit

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as Response

PASSWORD = "correct-horse-battery"
DJANGO_MESSAGE = (
    "Please enter a correct username and password. Note that both fields may be case-sensitive."
)
LOCKED = "Too many failed sign-in attempts. Try again in 15 minutes."
START = 2_000_000.0


class Clock:
    def __init__(self, mocker: MockerFixture) -> None:
        self.value = START
        mocker.patch("reviews.login_limit.now", side_effect=lambda: self.value)


@pytest.fixture(autouse=True)
def clean_cache() -> Iterator[None]:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="demo", password=PASSWORD)


@pytest.fixture
def clock(mocker: MockerFixture) -> Clock:
    return Clock(mocker)


def post(client: Client, username: str, password: str) -> "Response":
    return client.post("/login/", {"username": username, "password": password})


def error_box(response: "Response") -> str:
    html = response.content.decode()
    start = html.index("signin-error")
    return html[start : html.index("</div>", start)]


def lock_demo(client: Client) -> None:
    for _ in range(5):
        post(client, "demo", "wrong")


# M6


def test_five_wrong_passwords_each_show_the_django_message(user: User, clock: Clock) -> None:
    client = Client()

    for _ in range(5):
        response = post(client, "demo", "wrong")
        assert response.status_code == 200
        assert DJANGO_MESSAGE in error_box(response)
        assert LOCKED not in response.content.decode()


# M7


def test_right_password_with_no_failure_redirects_to_dashboard(user: User, clock: Clock) -> None:
    response = post(Client(), "demo", PASSWORD)

    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"


# M8


def test_right_password_within_15_minutes_of_the_lock_is_refused(user: User, clock: Clock) -> None:
    client = Client()
    lock_demo(client)

    clock.value = START + 899
    response = post(client, "demo", PASSWORD)
    html = response.content.decode()

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    assert LOCKED in error_box(response)
    assert DJANGO_MESSAGE not in html
    assert 'value="demo"' in html
    assert PASSWORD not in html


def test_unknown_username_locks_with_the_same_message(db: None, clock: Clock) -> None:
    client = Client()
    for _ in range(5):
        response = post(client, "no-such-user", "wrong")
        assert DJANGO_MESSAGE in error_box(response)

    response = post(client, "no-such-user", "wrong")

    assert response.status_code == 200
    assert LOCKED in error_box(response)
    assert DJANGO_MESSAGE not in response.content.decode()


def test_username_case_and_spaces_share_the_lock(user: User, clock: Clock) -> None:
    client = Client()
    for name in ("Demo ", "DEMO", " demo", "demo", "DeMo"):
        post(client, name, "wrong")

    response = post(client, "demo", PASSWORD)

    assert LOCKED in error_box(response)
    assert "_auth_user_id" not in client.session


def test_full_width_spelling_of_a_locked_username_is_refused_too(user: User, clock: Clock) -> None:
    client = Client()
    lock_demo(client)

    response = post(client, "ｄemo", PASSWORD)

    assert response.status_code == 200
    assert LOCKED in error_box(response)
    assert "_auth_user_id" not in client.session


def test_empty_fields_while_locked_show_only_required_errors(user: User, clock: Clock) -> None:
    client = Client()
    lock_demo(client)

    response = post(client, "", "")
    html = response.content.decode()

    assert html.count("This field is required.") == 2
    assert LOCKED not in html


# M9


def test_right_password_after_900_seconds_signs_in_and_resets_the_count(
    user: User, clock: Clock
) -> None:
    client = Client()
    lock_demo(client)

    clock.value = START + 900
    response = post(client, "demo", PASSWORD)
    assert response.status_code == 302
    assert response["Location"] == "/dashboard/"

    client.post("/logout/")
    wrong = post(client, "demo", "wrong")
    assert DJANGO_MESSAGE in error_box(wrong)
    assert LOCKED not in wrong.content.decode()


# M13


def test_wrong_password_makes_one_query(
    user: User, clock: Clock, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    client = Client()

    with django_assert_num_queries(1):
        response = post(client, "demo", "wrong")

    assert response.status_code == 200


def test_right_password_makes_nine_queries(
    user: User, clock: Clock, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    client = Client()

    with django_assert_num_queries(9):
        response = post(client, "demo", PASSWORD)

    assert response.status_code == 302


def test_locked_attempt_makes_no_query(
    user: User, clock: Clock, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    client = Client()
    lock_demo(client)
    assert login_limit.is_locked("demo") is True

    with django_assert_num_queries(0):
        response = post(client, "demo", PASSWORD)

    assert response.status_code == 200
    assert LOCKED in error_box(response)
