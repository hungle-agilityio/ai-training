import re
from collections.abc import Iterator
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from pytest_mock import MockerFixture

STRONG = "correct-horse-battery"
OTHER_STRONG = "violet-lantern-harbor"
PROMPT = "reviews.management.commands.create_user.getpass"
BLUEPRINT = Path(__file__).resolve().parents[4] / "render.yaml"


def answers(mocker: MockerFixture, *typed: str) -> MagicMock:
    replies: Iterator[str] = iter(typed)
    return mocker.patch(PROMPT, side_effect=lambda prompt="": next(replies))


def create_user(username: str) -> str:
    out = StringIO()
    call_command("create_user", username, stdout=out)
    return out.getvalue()


def seed() -> str:
    out = StringIO()
    call_command("seed_demo_data", stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_create_user_makes_an_active_user_who_is_not_staff(mocker: MockerFixture) -> None:
    prompt = answers(mocker, STRONG, STRONG)

    output = create_user("anna")

    user = get_user_model().objects.get(username="anna")
    assert user.is_active and not user.is_staff and not user.is_superuser
    assert user.check_password(STRONG)
    assert output.strip() == "Created user anna."
    assert prompt.call_count == 2


@pytest.mark.django_db
def test_create_user_refuses_an_existing_username(mocker: MockerFixture) -> None:
    get_user_model().objects.create_user(username="anna", password=OTHER_STRONG)
    answers(mocker, STRONG, STRONG)

    with pytest.raises(CommandError, match="^User anna already exists.$"):
        create_user("anna")

    assert get_user_model().objects.get(username="anna").check_password(OTHER_STRONG)


@pytest.mark.django_db
def test_create_user_refuses_two_different_passwords(mocker: MockerFixture) -> None:
    answers(mocker, STRONG, OTHER_STRONG)

    with pytest.raises(CommandError, match="^The two passwords differ.$"):
        create_user("anna")

    assert not get_user_model().objects.filter(username="anna").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("weak", ["short", "12345678901", "password123"])
def test_create_user_refuses_a_password_the_validators_reject(
    mocker: MockerFixture, weak: str
) -> None:
    answers(mocker, weak, weak)

    with pytest.raises(CommandError) as refused:
        create_user("anna")

    assert "\n" not in str(refused.value)
    assert not get_user_model().objects.filter(username="anna").exists()


@pytest.mark.django_db
def test_seed_creates_the_demo_user_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REVIEWRADAR_DEMO_PASSWORD", STRONG)

    output = seed()

    demo: User = get_user_model().objects.get(username="demo")
    assert demo.check_password(STRONG) and demo.is_active and not demo.is_staff
    assert "Demo user: demo" in output
    assert STRONG not in output


@pytest.mark.django_db
def test_seed_sets_the_password_of_an_existing_demo_user(monkeypatch: pytest.MonkeyPatch) -> None:
    get_user_model().objects.create_user(username="demo", password=OTHER_STRONG)
    monkeypatch.setenv("REVIEWRADAR_DEMO_PASSWORD", STRONG)

    seed()

    assert get_user_model().objects.filter(username="demo").count() == 1
    assert get_user_model().objects.get(username="demo").check_password(STRONG)


@pytest.mark.django_db
@pytest.mark.parametrize("value", [None, ""])
def test_seed_without_the_password_makes_no_demo_user(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("REVIEWRADAR_DEMO_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("REVIEWRADAR_DEMO_PASSWORD", value)

    output = seed()

    assert "REVIEWRADAR_DEMO_PASSWORD is not set; no demo user." in output
    assert not get_user_model().objects.filter(username="demo").exists()
    assert "Seeded 3 branches." in output


@pytest.mark.django_db
def test_seed_never_changes_or_deletes_another_user(monkeypatch: pytest.MonkeyPatch) -> None:
    get_user_model().objects.create_user(username="anna", password=OTHER_STRONG)
    monkeypatch.setenv("REVIEWRADAR_DEMO_PASSWORD", STRONG)

    seed()
    seed()

    assert get_user_model().objects.count() == 2
    assert get_user_model().objects.get(username="anna").check_password(OTHER_STRONG)


def test_render_blueprint_asks_for_the_demo_password_without_a_value() -> None:
    entry = re.search(
        r"^(\s*)- key: REVIEWRADAR_DEMO_PASSWORD\n((?:\1  .*\n?)*)", BLUEPRINT.read_text(), re.M
    )

    assert entry is not None
    assert entry.group(2).split() == ["sync:", "false"]
