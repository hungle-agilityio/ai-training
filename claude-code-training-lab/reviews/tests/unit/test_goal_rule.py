from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from reviews.goals import GoalStatus, goal_status


@pytest.mark.parametrize("score", [None, 0.0, 4.5])
def test_no_goal_gives_a_dash_whatever_the_score(score: float | None) -> None:
    status = goal_status(score, None)
    assert status == GoalStatus(goal=None, met=None, short_by=None, label="–")


def test_goal_without_score_says_no_score_yet() -> None:
    status = goal_status(None, Decimal("4.0"))
    assert (status.met, status.short_by, status.label) == (None, None, "No score yet")
    assert status.goal == Decimal("4.0")


@pytest.mark.parametrize(("score", "goal"), [(4.0, "4.0"), (4.5, "4.0"), (5.0, "1.0")])
def test_score_at_or_above_goal_is_met(score: float, goal: str) -> None:
    status = goal_status(score, Decimal(goal))
    assert (status.met, status.short_by, status.label) == (True, None, "Met")


@pytest.mark.parametrize(
    ("score", "goal", "short", "label"),
    [
        (4.0, "4.5", "0.5", "0.5 short"),
        (2.0, "3.0", "1.0", "1.0 short"),
        (3.9, "4.0", "0.1", "0.1 short"),
        (4.3, "4.4", "0.1", "0.1 short"),
    ],
)
def test_score_below_goal_is_short_by_exact_decimal(
    score: float, goal: str, short: str, label: str
) -> None:
    status = goal_status(score, Decimal(goal))
    assert status.met is False
    assert isinstance(status.short_by, Decimal)
    assert status.short_by == Decimal(short)
    assert str(status.short_by) == short
    assert status.label == label


def test_goal_status_is_frozen() -> None:
    status = goal_status(4.0, Decimal("4.0"))
    with pytest.raises(FrozenInstanceError):
        status.met = False  # type: ignore[misc]
