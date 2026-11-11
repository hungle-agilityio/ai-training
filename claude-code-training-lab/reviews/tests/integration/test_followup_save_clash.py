from datetime import UTC, datetime
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from pytest_mock import MockerFixture

from reviews import followup_repository, repositories
from reviews.models import Branch, Business, Review, ReviewFollowUp

FIRST = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 3, 15, 30, tzinfo=UTC)


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


@pytest.fixture
def review(branch: Branch) -> Review:
    return repositories.create_review(
        branch=branch, rating=1, text="Waited an hour.", created_at=FIRST
    )


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="anna", password="x")


@pytest.fixture
def other(db: None) -> User:
    return get_user_model().objects.create_user(username="binh", password="x")


def stored() -> list[tuple[int, str, str, int | None, datetime]]:
    return list(
        ReviewFollowUp.objects.values_list(
            "review_id", "status", "note", "updated_by_id", "updated_at"
        )
    )


def someone_else_saves_first(mocker: MockerFixture, review: Review, other: User) -> None:
    """Another save creates the record just before this save writes."""
    write = repositories.upsert_followup

    def clash(**values: Any) -> None:
        ReviewFollowUp.objects.create(
            review=review, status="contacted", note="Theirs.", updated_by=other, updated_at=FIRST
        )
        write(**values)

    mocker.patch.object(followup_repository, "upsert_followup", side_effect=clash)


def test_clash_on_the_first_save_updates_the_record_of_the_other_save(
    review: Review, user: User, other: User, mocker: MockerFixture
) -> None:
    someone_else_saves_first(mocker, review, other)

    followup_repository.save_followup(
        review_id=review.id, status="resolved", note="Mine.", user_id=user.id, now=LATER
    )

    assert stored() == [(review.id, "resolved", "Mine.", user.id, LATER)]


@pytest.mark.login
def test_clash_on_the_page_redirects_with_the_saved_notice(
    review: Review, user: User, other: User, mocker: MockerFixture
) -> None:
    someone_else_saves_first(mocker, review, other)
    client = Client()
    client.force_login(user)

    response = client.post(
        f"/reviews/{review.id}/follow-up/", {"status": "resolved", "note": "Mine."}
    )

    assert response.status_code == 302
    assert "Follow-up saved." in client.get(response["Location"]).content.decode()
    assert [(row[0], row[1], row[2], row[3]) for row in stored()] == [
        (review.id, "resolved", "Mine.", user.id)
    ]


def test_first_save_stores_one_record_with_the_given_values(review: Review, user: User) -> None:
    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="Called.", user_id=user.id, now=FIRST
    )

    assert stored() == [(review.id, "contacted", "Called.", user.id, FIRST)]


def test_later_save_replaces_status_note_user_and_time(
    review: Review, user: User, other: User
) -> None:
    followup_repository.save_followup(
        review_id=review.id, status="contacted", note="Called.", user_id=user.id, now=FIRST
    )
    first_id = ReviewFollowUp.objects.get().id

    followup_repository.save_followup(
        review_id=review.id, status="resolved", note="", user_id=None, now=LATER
    )

    assert stored() == [(review.id, "resolved", "", None, LATER)]
    assert ReviewFollowUp.objects.get().id == first_id


def test_save_of_one_review_leaves_the_record_of_another_alone(
    branch: Branch, review: Review, user: User
) -> None:
    second = repositories.create_review(branch=branch, rating=2, text="Cold.", created_at=FIRST)
    followup_repository.save_followup(
        review_id=second.id, status="contacted", note="Two.", user_id=None, now=FIRST
    )

    followup_repository.save_followup(
        review_id=review.id, status="resolved", note="One.", user_id=user.id, now=LATER
    )

    assert sorted(stored()) == [
        (review.id, "resolved", "One.", user.id, LATER),
        (second.id, "contacted", "Two.", None, FIRST),
    ]


def test_first_save_takes_at_most_two_queries_and_a_later_one_takes_one(review: Review) -> None:
    with CaptureQueriesContext(connection) as creating:
        followup_repository.save_followup(
            review_id=review.id, status="contacted", note="", user_id=None, now=FIRST
        )
    with CaptureQueriesContext(connection) as updating:
        followup_repository.save_followup(
            review_id=review.id, status="resolved", note="", user_id=None, now=LATER
        )

    assert len(creating) <= 2
    assert len(updating) == 1
