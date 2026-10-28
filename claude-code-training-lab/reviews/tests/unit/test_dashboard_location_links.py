import pytest

from reviews.models import Branch, Business
from reviews.services import dashboard_overview


@pytest.mark.django_db
def test_branch_row_carries_the_location_id_with_and_without_reviews() -> None:
    business = Business.objects.create(name="Demo")
    empty = Branch.objects.create(business=business, name="Newtown")

    overview = dashboard_overview()

    assert [row.branch_id for row in overview.branches] == [empty.id]
