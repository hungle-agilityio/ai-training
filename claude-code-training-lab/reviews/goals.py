from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

NO_GOAL_LABEL = "–"
NO_SCORE_LABEL = "No score yet"
MET_LABEL = "Met"
ONE_DECIMAL = Decimal("0.1")


@dataclass(frozen=True)
class GoalStatus:
    goal: Decimal | None
    met: bool | None
    short_by: Decimal | None
    label: str


def goal_status(score: float | None, goal: Decimal | None) -> GoalStatus:
    """A location meets its goal when score >= goal; otherwise it is short by the gap."""
    if goal is None:
        return GoalStatus(goal=None, met=None, short_by=None, label=NO_GOAL_LABEL)
    if score is None:
        return GoalStatus(goal=goal, met=None, short_by=None, label=NO_SCORE_LABEL)
    exact_score = Decimal(str(score))
    if exact_score >= goal:
        return GoalStatus(goal=goal, met=True, short_by=None, label=MET_LABEL)
    short_by = (goal - exact_score).quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)
    return GoalStatus(goal=goal, met=False, short_by=short_by, label=f"{short_by} short")
