from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from reviews import goal_repository
from reviews.models import Branch, Business


@pytest.fixture
def business() -> Business:
    return Business.objects.create(name="Clinics")


@pytest.mark.django_db
def test_new_branch_has_no_goal(business: Business) -> None:
    branch = Branch.objects.create(business=business, name="A")

    assert Branch.objects.get(id=branch.id).target_score is None


@pytest.mark.django_db
def test_goals_are_ordered_by_name_then_id_in_one_query(business: Business) -> None:
    first_b = Branch.objects.create(business=business, name="B", target_score=Decimal("4.5"))
    second_b = Branch.objects.create(business=business, name="B")
    a = Branch.objects.create(business=business, name="A")

    with CaptureQueriesContext(connection) as queries:
        goals = goal_repository.location_goals()

    assert len(queries) == 1
    assert [g.location_id for g in goals] == [a.id, first_b.id, second_b.id]
    assert [g.name for g in goals] == ["A", "B", "B"]
    assert goals[1].goal == Decimal("4.5")
    assert isinstance(goals[1].goal, Decimal)
    assert goals[0].goal is None


@pytest.mark.django_db
def test_save_goals_sets_and_clears(business: Business) -> None:
    a = Branch.objects.create(business=business, name="A", target_score=Decimal("3.0"))
    b = Branch.objects.create(business=business, name="B")

    goal_repository.save_goals({a.id: None, b.id: Decimal("4.0")})

    assert Branch.objects.get(id=a.id).target_score is None
    assert Branch.objects.get(id=b.id).target_score == Decimal("4.0")


@pytest.mark.django_db
def test_save_goals_updates_only_changed_locations(business: Business) -> None:
    a = Branch.objects.create(business=business, name="A", target_score=Decimal("3.0"))
    b = Branch.objects.create(business=business, name="B")

    with CaptureQueriesContext(connection) as queries:
        goal_repository.save_goals({a.id: Decimal("3.0"), b.id: Decimal("4.0")})

    updates = [q for q in queries if q["sql"].lstrip().upper().startswith("UPDATE")]
    assert len(updates) == 1
    assert Branch.objects.get(id=b.id).target_score == Decimal("4.0")


@pytest.mark.django_db
def test_save_goals_ignores_unknown_location(business: Business) -> None:
    a = Branch.objects.create(business=business, name="A")

    goal_repository.save_goals({a.id + 999: Decimal("4.0")})

    assert Branch.objects.get(id=a.id).target_score is None
