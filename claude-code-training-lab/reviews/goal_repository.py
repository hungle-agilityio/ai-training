from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from reviews.models import Branch


@dataclass(frozen=True)
class LocationGoal:
    location_id: int
    name: str
    goal: Decimal | None


def location_goals() -> list[LocationGoal]:
    """Goals of all locations, ordered by name then id, in one query."""
    rows = Branch.objects.order_by("name", "id").values_list("id", "name", "target_score")
    return [LocationGoal(location_id=i, name=n, goal=g) for i, n, g in rows]


def save_goals(goals: dict[int, Decimal | None]) -> None:
    """Save goals (location id to goal) in one transaction, updating only the changed ones."""
    with transaction.atomic():
        current = dict(Branch.objects.filter(id__in=goals).values_list("id", "target_score"))
        for location_id, goal in goals.items():
            if location_id in current and current[location_id] != goal:
                Branch.objects.filter(id=location_id).update(target_score=goal)
