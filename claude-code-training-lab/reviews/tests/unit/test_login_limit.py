from collections.abc import Iterator

import pytest
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import resolve
from pytest_mock import MockerFixture

from reviews import login_limit
from reviews.forms import LimitedAuthenticationForm

PASSWORD = "correct-horse-battery"
START = 1_000_000.0


@pytest.fixture(autouse=True)
def clean_cache() -> Iterator[None]:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="demo", password=PASSWORD)


@pytest.fixture
def clock(mocker: MockerFixture) -> "Clock":
    return Clock(mocker, START)


class Clock:
    def __init__(self, mocker: MockerFixture, start: float) -> None:
        self.value = start
        mocker.patch("reviews.login_limit.now", side_effect=lambda: self.value)

    def set(self, value: float) -> None:
        self.value = value


def fail_times(username: str, times: int) -> None:
    for _ in range(times):
        login_limit.record_failure(username)


def make_form(username: str, password: str) -> LimitedAuthenticationForm:
    return LimitedAuthenticationForm(None, data={"username": username, "password": password})


# M12: constants, wiring, authenticate never called when locked


def test_constants_hold_the_agreed_values() -> None:
    assert login_limit.MAX_FAILURES == 5
    assert login_limit.WINDOW_SECONDS == 900
    assert login_limit.LOCK_SECONDS == 900
    assert (
        login_limit.LOCKED_MESSAGE == "Too many failed sign-in attempts. Try again in 15 minutes."
    )


def test_now_returns_the_wall_clock_as_a_float(mocker: MockerFixture) -> None:
    mocker.patch("time.time", return_value=123.5)

    assert login_limit.now() == 123.5


def test_login_view_uses_the_limited_authentication_form() -> None:
    match = resolve("/login/")

    assert match.func.view_initkwargs["authentication_form"] is LimitedAuthenticationForm  # type: ignore[attr-defined]
    assert match.func.view_initkwargs["redirect_authenticated_user"] is True  # type: ignore[attr-defined]


def test_locked_form_never_calls_authenticate(
    user: User, clock: Clock, mocker: MockerFixture
) -> None:
    fail_times("demo", 5)
    spy = mocker.spy(auth_forms, "authenticate")

    form = make_form("demo", PASSWORD)

    assert form.is_valid() is False
    assert spy.call_count == 0
    errors = form.non_field_errors().as_data()
    assert errors[0].code == "locked"
    assert errors[0].message == login_limit.LOCKED_MESSAGE


def test_form_counts_a_wrong_password_and_locks_on_the_fifth(user: User, clock: Clock) -> None:
    for _ in range(5):
        form = make_form("demo", "wrong")
        assert form.is_valid() is False
        assert form.non_field_errors().as_data()[0].code == "invalid_login"

    assert login_limit.is_locked("demo") is True


def test_form_success_resets_the_count(user: User, clock: Clock) -> None:
    fail_times("demo", 4)

    assert make_form("demo", PASSWORD).is_valid() is True

    fail_times("demo", 4)
    assert login_limit.is_locked("demo") is False


def test_form_with_empty_password_does_not_count_or_check_the_lock(
    user: User, clock: Clock, mocker: MockerFixture
) -> None:
    spy = mocker.spy(login_limit, "record_failure")
    form = make_form("demo", "")

    assert form.is_valid() is False
    assert "password" in form.errors
    assert form.non_field_errors() == []
    assert spy.call_count == 0
    fail_times("demo", 4)
    assert login_limit.is_locked("demo") is False


def test_form_with_empty_password_on_a_locked_username_shows_only_the_field_error(
    user: User, clock: Clock
) -> None:
    fail_times("demo", 5)
    form = make_form("demo", "")

    assert form.is_valid() is False
    assert "password" in form.errors
    assert form.non_field_errors() == []


def test_full_width_spelling_shares_the_count_of_the_username_django_signs_in(
    clock: Clock,
) -> None:
    fail_times("ｄemo", 5)

    assert login_limit.is_locked("demo") is True
    assert login_limit.is_locked("dｅmo") is True


def test_form_with_empty_username_shows_no_lock_message_even_if_others_are_locked(
    db: None, clock: Clock
) -> None:
    fail_times("", 10)
    form = make_form("", "wrong")

    assert form.is_valid() is False
    assert "username" in form.errors
    assert login_limit.LOCKED_MESSAGE not in str(form.errors)


# M10: normalisation, unknown usernames, attempts while locked


def test_five_failures_lock_the_username(clock: Clock) -> None:
    fail_times("demo", 4)
    assert login_limit.is_locked("demo") is False

    login_limit.record_failure("demo")

    assert login_limit.is_locked("demo") is True


def test_demo_with_spaces_and_case_variants_share_one_count(clock: Clock) -> None:
    login_limit.record_failure("Demo ")
    login_limit.record_failure("DEMO")
    login_limit.record_failure(" demo")
    login_limit.record_failure("demo")
    login_limit.record_failure("DeMo")

    assert login_limit.is_locked("demo") is True
    assert login_limit.is_locked(" DEMO ") is True


def test_username_without_account_locks_after_five_failures(clock: Clock) -> None:
    fail_times("no-such-user", 5)

    assert login_limit.is_locked("no-such-user") is True
    assert login_limit.is_locked("another-user") is False


def test_other_usernames_are_not_affected_by_a_lock(clock: Clock) -> None:
    fail_times("demo", 5)

    assert login_limit.is_locked("other") is False


def test_username_with_odd_characters_is_a_valid_cache_key(clock: Clock) -> None:
    odd = "na me\n\x00é" + "x" * 500

    fail_times(odd, 5)

    assert login_limit.is_locked(odd) is True


def test_state_is_kept_in_the_default_cache_under_a_hashed_key(clock: Clock) -> None:
    import hashlib

    login_limit.record_failure("Demo ")

    digest = hashlib.sha256(b"demo").hexdigest()
    assert cache.get(f"login-limit:{digest}") is not None


def test_lock_lasts_900_seconds_from_the_fifth_failure(clock: Clock) -> None:
    fail_times("demo", 5)

    clock.set(START + 899)
    assert login_limit.is_locked("demo") is True

    clock.set(START + 900)
    assert login_limit.is_locked("demo") is False


def test_failures_while_locked_are_not_counted_and_do_not_extend_the_lock(clock: Clock) -> None:
    fail_times("demo", 5)

    clock.set(START + 600)
    fail_times("demo", 10)

    clock.set(START + 900)
    assert login_limit.is_locked("demo") is False
    login_limit.record_failure("demo")
    assert login_limit.is_locked("demo") is False


# M11: reset, window, locked record_failure


def test_success_between_failures_resets_the_count(clock: Clock) -> None:
    fail_times("demo", 4)
    login_limit.record_success("demo")
    fail_times("demo", 4)

    assert login_limit.is_locked("demo") is False


def test_record_success_normalises_the_username(clock: Clock) -> None:
    fail_times("demo", 4)
    login_limit.record_success(" DEMO ")
    login_limit.record_failure("demo")

    assert login_limit.is_locked("demo") is False


def test_failure_900_seconds_after_the_first_starts_the_count_again(clock: Clock) -> None:
    fail_times("demo", 4)

    clock.set(START + 900)
    login_limit.record_failure("demo")

    assert login_limit.is_locked("demo") is False
    fail_times("demo", 3)
    assert login_limit.is_locked("demo") is False
    login_limit.record_failure("demo")
    assert login_limit.is_locked("demo") is True


def test_failure_just_inside_the_window_still_counts(clock: Clock) -> None:
    fail_times("demo", 4)

    clock.set(START + 899)
    login_limit.record_failure("demo")

    assert login_limit.is_locked("demo") is True


def test_record_failure_on_a_locked_username_changes_nothing(clock: Clock) -> None:
    fail_times("demo", 5)
    before = cache.get(f"login-limit:{__import__('hashlib').sha256(b'demo').hexdigest()}")

    clock.set(START + 300)
    login_limit.record_failure("demo")

    after = cache.get(f"login-limit:{__import__('hashlib').sha256(b'demo').hexdigest()}")
    assert after == before


def test_record_success_on_a_fresh_username_does_nothing_harmful(clock: Clock) -> None:
    login_limit.record_success("never-seen")

    assert login_limit.is_locked("never-seen") is False


def test_success_after_the_lock_expired_clears_the_count(clock: Clock) -> None:
    fail_times("demo", 5)
    clock.set(START + 900)
    login_limit.record_success("demo")

    fail_times("demo", 4)

    assert login_limit.is_locked("demo") is False
