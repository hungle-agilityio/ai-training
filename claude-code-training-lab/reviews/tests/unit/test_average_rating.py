from reviews.models import Review
from reviews.services import average_rating


def _reviews(*ratings: int) -> list[Review]:
    return [Review(rating=rating) for rating in ratings]


def test_average_of_identical_ratings() -> None:
    assert average_rating(_reviews(4, 4)) == 4


def test_average_of_single_review() -> None:
    assert average_rating(_reviews(5)) == 5


def test_average_of_mixed_ratings_keeps_one_decimal() -> None:
    # BUG-001: 4, 5, 2 must give 3.7 (11 / 3 = 3.67 rounded to one decimal), not 3
    assert average_rating(_reviews(4, 5, 2)) == 3.7
