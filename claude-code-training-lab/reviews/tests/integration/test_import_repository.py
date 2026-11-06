from datetime import UTC, datetime

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews import import_repository
from reviews.import_service import import_reviews
from reviews.models import Branch, Business, Review
from reviews.services import ReviewFilters, reviews_csv

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)


def _branch(name: str = "Riverside") -> Branch:
    business = Business.objects.filter(name="Demo").first() or Business.objects.create(name="Demo")
    return Branch.objects.create(business=business, name=name)


def test_300_rows_take_at_most_10_queries(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    _branch()
    rows = "".join(
        f"Riverside,{(i % 5) + 1},review {i},2026-10-{(i % 28) + 1:02d} {i % 24:02d}:{i % 60:02d}\n"
        for i in range(300)
    )
    data = ("Location,Rating,Review text,Date\n" + rows).encode()

    with django_assert_max_num_queries(10):
        result = import_reviews(data, now=NOW)

    assert result.imported == 300
    assert Review.objects.count() == 300


def test_saved_rows_are_searchable_like_create_review() -> None:
    branch = _branch()

    count = import_repository.save_new_reviews(
        [import_repository.NewReview(branch.pk, 5, "Dịch Vụ TỐT", NOW)]
    )

    assert count == 1
    assert Review.objects.get().search_text == "dịch vụ tốt"


def test_lowest_id_wins_for_the_same_name() -> None:
    first = _branch("Spa")
    _branch("SPA")

    assert import_repository.location_ids_by_name()["spa"] == first.pk


def test_existing_keys_are_read_in_one_query(
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    branch = _branch()
    Review.objects.create(branch=branch, rating=5, text="a", created_at=NOW)

    with django_assert_num_queries(1):
        keys = import_repository.existing_keys({branch.pk}, NOW, NOW)

    assert keys == {(branch.pk, NOW, 5, "a")}


def test_exported_file_imports_back_as_all_duplicates() -> None:
    branch = _branch()
    for rating, text in ((5, "=SUM(1)"), (4, "Dịch vụ tốt"), (3, ""), (2, "-dash")):
        Review.objects.create(
            branch=branch,
            rating=rating,
            text=text,
            created_at=datetime(2026, 11, 1, rating, 0, tzinfo=UTC),
        )
    exported = "".join(reviews_csv(ReviewFilters())).encode("utf-8")

    result = import_reviews(exported, now=NOW)

    assert (result.imported, result.duplicates, result.errors) == (0, 4, ())
    assert Review.objects.count() == 4
