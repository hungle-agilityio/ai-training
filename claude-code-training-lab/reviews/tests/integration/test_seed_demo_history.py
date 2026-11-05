from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from pytest_mock import MockerFixture

from reviews.models import Review

FIXED_NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
STEP_DAYS = 20


def seed(mocker: MockerFixture, *args: str) -> None:
    mocker.patch("reviews.management.commands.seed_demo_data.timezone.now", return_value=FIXED_NOW)
    call_command("seed_demo_data", *args, stdout=StringIO())


def days_back(branch_name: str) -> list[int]:
    created = Review.objects.filter(branch__name=branch_name).order_by("-created_at")
    return [(FIXED_NOW - review.created_at).days for review in created]


@pytest.mark.django_db
def test_default_reviews_are_twenty_days_apart_newest_today(mocker: MockerFixture) -> None:
    seed(mocker)

    assert days_back("Airport") == [0, 20, 40, 60]
    assert days_back("Downtown") == [0, 20, 40, 60, 80]
    assert days_back("Riverside") == [0, 20, 40, 60, 80]


@pytest.mark.django_db
def test_oldest_default_review_is_eighty_days_old(mocker: MockerFixture) -> None:
    seed(mocker)

    oldest = Review.objects.order_by("created_at").first()
    assert oldest is not None
    assert FIXED_NOW - oldest.created_at == timedelta(days=4 * STEP_DAYS)


@pytest.mark.django_db
def test_extra_branches_follow_the_same_spacing(mocker: MockerFixture) -> None:
    seed(mocker, "--branches", "2")

    assert days_back("Extra 1") == [0, 20, 40]
    assert days_back("Extra 2") == [0, 20, 40]


@pytest.mark.django_db
def test_reviews_fall_in_at_least_three_different_months(mocker: MockerFixture) -> None:
    seed(mocker)

    months = {(r.created_at.year, r.created_at.month) for r in Review.objects.all()}
    assert len(months) >= 3
