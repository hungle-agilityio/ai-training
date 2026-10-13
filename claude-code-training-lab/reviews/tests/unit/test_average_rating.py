from reviews.models import Review
from reviews.services import average_rating


def _reviews(*ratings: int) -> list[Review]:
    return [Review(rating=rating) for rating in ratings]


def test_average_of_identical_ratings() -> None:
    assert average_rating(_reviews(4, 4)) == 4


def test_average_of_single_review() -> None:
    assert average_rating(_reviews(5)) == 5
