from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from reviews import location_repository, repositories
from reviews.models import Branch, Business, Review


@pytest.fixture
def business() -> Business:
    return Business.objects.create(name="Clinics")


@pytest.mark.django_db
def test_add_location_joins_the_existing_business_and_returns_its_id(business: Business) -> None:
    location_id = location_repository.add_location("Downtown")

    assert isinstance(location_id, int)
    location = Branch.objects.get(id=location_id)
    assert location.name == "Downtown"
    assert location.business_id == business.id
    assert location.target_score is None
    assert Business.objects.count() == 1


@pytest.mark.django_db
def test_add_location_uses_the_business_with_the_lowest_id(business: Business) -> None:
    Business.objects.create(name="Spas")

    location_id = location_repository.add_location("Downtown")

    assert Branch.objects.get(id=location_id).business_id == business.id
    assert Business.objects.count() == 2


@pytest.mark.django_db
def test_first_location_creates_my_business() -> None:
    location_id = location_repository.add_location("Downtown")

    created = Business.objects.get()
    assert created.name == "My business"
    assert Branch.objects.get(id=location_id).business_id == created.id


@pytest.mark.django_db
def test_second_location_reuses_the_created_business() -> None:
    location_repository.add_location("Downtown")
    location_repository.add_location("Riverside")

    assert Business.objects.count() == 1
    assert Branch.objects.count() == 2


@pytest.mark.django_db
def test_rename_changes_only_the_name(business: Business) -> None:
    location = Branch.objects.create(
        business=business, name="Downtown", target_score=Decimal("4.5")
    )
    other = Branch.objects.create(business=business, name="Riverside")
    created_at = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
    first = Review.objects.create(branch=location, rating=5, text="Great", created_at=created_at)
    second = Review.objects.create(branch=location, rating=2, text="Slow", created_at=created_at)
    before = repositories.branch_rating_totals_for(location.id)
    assert before is not None

    location_repository.rename_location(location.id, "Old Town")

    renamed = Branch.objects.get(id=location.id)
    assert renamed.name == "Old Town"
    assert renamed.business_id == business.id
    assert renamed.target_score == Decimal("4.5")
    assert isinstance(renamed.target_score, Decimal)
    assert list(
        Review.objects.filter(branch_id=location.id).order_by("id").values_list("id", "rating")
    ) == [(first.id, 5), (second.id, 2)]
    after = repositories.branch_rating_totals_for(location.id)
    assert after is not None
    assert (after.review_count, after.rating_total) == (before.review_count, before.rating_total)
    assert Branch.objects.get(id=other.id).name == "Riverside"


@pytest.mark.django_db
def test_rename_runs_one_update_that_sets_only_the_name(business: Business) -> None:
    location = Branch.objects.create(business=business, name="Downtown")

    with CaptureQueriesContext(connection) as queries:
        location_repository.rename_location(location.id, "Old Town")

    assert len(queries) == 1
    sql = queries[0]["sql"]
    assert sql.lstrip().upper().startswith("UPDATE")
    assert "target_score" not in sql
    assert "business_id" not in sql


@pytest.mark.django_db
def test_rename_of_a_missing_location_changes_nothing(business: Business) -> None:
    location = Branch.objects.create(business=business, name="Downtown")

    location_repository.rename_location(location.id + 1, "Old Town")

    assert list(Branch.objects.values_list("name", flat=True)) == ["Downtown"]


@pytest.mark.django_db
def test_get_location_returns_id_and_name_in_one_query(business: Business) -> None:
    location = Branch.objects.create(business=business, name="Downtown")

    with CaptureQueriesContext(connection) as queries:
        found = location_repository.get_location(location.id)

    assert len(queries) == 1
    assert found == location_repository.Location(location_id=location.id, name="Downtown")
    assert found is not None
    assert isinstance(found.location_id, int)


@pytest.mark.django_db
def test_get_location_is_none_when_missing(business: Business) -> None:
    location = Branch.objects.create(business=business, name="Downtown")

    assert location_repository.get_location(location.id + 1) is None


@pytest.mark.django_db
def test_other_location_names_leaves_out_the_given_id_in_one_query(business: Business) -> None:
    downtown = Branch.objects.create(business=business, name="Downtown")
    Branch.objects.create(business=business, name="Riverside")
    Branch.objects.create(business=business, name="Airport")

    with CaptureQueriesContext(connection) as queries:
        names = location_repository.other_location_names(downtown.id)

    assert len(queries) == 1
    assert names == ["Airport", "Riverside"]


@pytest.mark.django_db
def test_other_location_names_query_count_does_not_grow_with_the_data(
    business: Business,
) -> None:
    first = Branch.objects.create(business=business, name="Location 000")
    Branch.objects.bulk_create(
        Branch(business=business, name=f"Location {number:03d}") for number in range(1, 200)
    )

    with CaptureQueriesContext(connection) as queries:
        names = location_repository.other_location_names(first.id)

    assert len(queries) == 1
    assert len(names) == 199
    assert "Location 000" not in names


@pytest.mark.django_db
def test_other_location_names_keeps_a_same_named_location(business: Business) -> None:
    downtown = Branch.objects.create(business=business, name="Downtown")
    Branch.objects.create(business=business, name="Downtown")

    assert location_repository.other_location_names(downtown.id) == ["Downtown"]


@pytest.mark.django_db
def test_other_location_names_is_empty_with_one_location(business: Business) -> None:
    only = Branch.objects.create(business=business, name="Downtown")

    assert location_repository.other_location_names(only.id) == []
