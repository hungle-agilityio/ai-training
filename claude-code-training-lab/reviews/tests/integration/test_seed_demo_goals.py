from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from reviews.models import Branch


def seed(*args: str) -> None:
    call_command("seed_demo_data", *args, stdout=StringIO())


def goals() -> dict[str, Decimal | None]:
    return dict(Branch.objects.values_list("name", "target_score"))


@pytest.mark.django_db
def test_default_seed_sets_demo_goals() -> None:
    seed()

    assert goals() == {"Airport": None, "Downtown": Decimal("4.5"), "Riverside": Decimal("3.0")}


@pytest.mark.django_db
def test_extra_and_new_locations_get_no_goal() -> None:
    seed("--branches", "2", "--with-new-branch")

    result = goals()
    assert result["Downtown"] == Decimal("4.5")
    for name in ("Extra 1", "Extra 2", "Newtown"):
        assert result[name] is None
