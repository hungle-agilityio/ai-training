from datetime import timedelta

from reviews import services
from reviews.repositories import BranchTotals

HOUR = 3600.0


def test_percent_is_whole_number_rounded_half_up() -> None:
    assert services.reply_share_percent(2, 3) == 67
    assert services.reply_share_percent(1, 8) == 13
    assert isinstance(services.reply_share_percent(1, 8), int)


def test_percent_is_none_without_counted_reviews() -> None:
    assert services.reply_share_percent(0, 0) is None


def test_average_hours_is_float_rounded_half_up_to_one_decimal() -> None:
    hours = services.average_reply_hours(53 * HOUR, 3)

    assert hours == 17.7
    assert isinstance(hours, float)


def test_average_hours_is_none_without_replies() -> None:
    assert services.average_reply_hours(0.0, 0) is None


def test_label_in_hours_under_48() -> None:
    assert services.reply_time_label(53 * HOUR, 3) == "17.7 h"


def test_label_in_days_from_48_hours() -> None:
    assert services.reply_time_label(48 * HOUR, 1) == "2.0 days"
    assert services.reply_time_label(74.5 * HOUR, 1) == "3.1 days"


def test_label_choice_uses_unrounded_hours() -> None:
    assert services.reply_time_label(47.96 * HOUR, 1) == "48.0 h"


def test_reply_speed_of_a_location_without_counted_reviews() -> None:
    speed = services.reply_speed_of(
        BranchTotals(branch_id=1, name="A", review_count=0, rating_total=0)
    )

    assert speed.percent is None
    assert speed.counted == 0
    assert speed.average_label == ""


def test_reply_speed_of_counted_reviews_with_no_reply() -> None:
    speed = services.reply_speed_of(
        BranchTotals(branch_id=1, name="A", review_count=2, rating_total=2, bad_counted=2)
    )

    assert speed.percent == 0
    assert speed.average_label == ""


def test_reply_speed_totals_sum_the_locations() -> None:
    day = timedelta(hours=24).total_seconds()
    speed = services.total_reply_speed(
        [
            BranchTotals(
                branch_id=1, name="A", review_count=2, rating_total=2,
                bad_counted=2, bad_replied=1, bad_replied_in_time=0, reply_seconds=day * 2,
            ),
            BranchTotals(
                branch_id=2, name="B", review_count=1, rating_total=1,
                bad_counted=1, bad_replied=1, bad_replied_in_time=1, reply_seconds=3 * HOUR,
            ),
        ]
    )

    assert (speed.counted, speed.replied_in_time, speed.percent) == (3, 1, 33)
    assert speed.average_label == "25.5 h"
