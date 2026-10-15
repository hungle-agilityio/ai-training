import pytest

from reviews.models import Review
from reviews.services import average_from_totals, average_rating, rounded_average


def _reviews(*ratings: int) -> list[Review]:
    return [Review(rating=rating) for rating in ratings]


def test_average_of_identical_ratings() -> None:
    assert average_rating(_reviews(4, 4)) == 4


def test_average_of_single_review() -> None:
    assert average_rating(_reviews(5)) == 5


def test_average_of_mixed_ratings_keeps_one_decimal() -> None:
    # Bug #1: 4, 5, 2 must give 3.7 (11 / 3 = 3.67 rounded to one decimal), not 3
    assert average_rating(_reviews(4, 5, 2)) == 3.7


def test_average_is_always_a_float() -> None:
    assert isinstance(average_rating(_reviews(4, 4)), float)


@pytest.mark.parametrize(
    ("ratings", "expected"),
    [
        ((2, 2, 2, 3), 2.3),  # 2.25 rounds half up, like Excel and a hand calculation
        ((3, 3, 3, 4), 3.3),  # 3.25
        ((1, 1, 1, 2), 1.3),  # 1.25
        ((4, 5, 2), 3.7),  # 3.67
        ((5, 4, 4), 4.3),  # 4.33
        ((2, 2, 3, 1), 2.0),
    ],
)
def test_average_rounds_half_up_to_one_decimal(ratings: tuple[int, ...], expected: float) -> None:
    assert average_rating(_reviews(*ratings)) == expected


def test_rounded_average_rounds_half_up() -> None:
    assert rounded_average(9, 4) == 2.3
    assert rounded_average(59, 20) == 3.0


def test_average_of_no_reviews_is_none() -> None:
    # A location without reviews has no score, and must not raise
    assert average_rating([]) is None


def test_average_from_totals_uses_the_same_rule() -> None:
    assert average_from_totals(0, 0) is None
    assert average_from_totals(9, 4) == 2.3
