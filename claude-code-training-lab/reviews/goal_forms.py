from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from reviews.goal_repository import LocationGoal

MIN_GOAL = Decimal("1.0")
MAX_GOAL = Decimal("5.0")
GOAL_ERROR = "Enter a score from 1.0 to 5.0 with one decimal."


def parse_goal(raw: str) -> Decimal | None:
    """Empty means no goal; anything else must be 1.0 to 5.0 with at most one decimal."""
    text = raw.strip()
    if not text:
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError(GOAL_ERROR) from None
    exponent = value.as_tuple().exponent
    if not value.is_finite() or not isinstance(exponent, int) or exponent < -1:
        raise ValueError(GOAL_ERROR)
    if not MIN_GOAL <= value <= MAX_GOAL:
        raise ValueError(GOAL_ERROR)
    return value


class GoalsForm:
    """Reads the goal-<location id> fields of the known locations; unknown fields are ignored."""

    def __init__(self, data: Mapping[str, str], locations: list[LocationGoal]) -> None:
        self.goals: dict[int, Decimal | None] = {}
        self.typed: dict[int, str] = {}
        self.errors: dict[int, str] = {}
        for location in locations:
            key = f"goal-{location.location_id}"
            if key not in data:
                continue
            raw = data[key]
            self.typed[location.location_id] = raw
            try:
                self.goals[location.location_id] = parse_goal(raw)
            except ValueError as error:
                self.errors[location.location_id] = str(error)

    def is_valid(self) -> bool:
        return not self.errors
