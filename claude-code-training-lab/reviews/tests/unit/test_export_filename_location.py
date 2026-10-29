from datetime import UTC, datetime

import pytest

from reviews.services import export_filename, location_slug

NOW = datetime(2026, 10, 29, 3, 0, tzinfo=UTC)


def test_name_without_location_stays_as_today() -> None:
    assert export_filename(NOW) == "reviews-2026-10-29.csv"


def test_name_carries_the_location_slug() -> None:
    assert export_filename(NOW, "riverside") == "reviews-riverside-2026-10-29.csv"


def test_date_is_the_vietnam_day_across_midnight_utc() -> None:
    late = datetime(2026, 10, 21, 17, 30, tzinfo=UTC)
    assert export_filename(late, "riverside") == "reviews-riverside-2026-10-22.csv"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Riverside", "riverside"),
        ("Quận 1 – Đà Nẵng", "quan-1-da-nang"),
        ("  Spa &  Salon!! ", "spa-salon"),
        ("đông", "dong"),
        ("ĐÔNG", "dong"),
    ],
)
def test_slug_lowercases_and_removes_accents(name: str, expected: str) -> None:
    assert location_slug(name, 7) == expected


@pytest.mark.parametrize("name", ["", "—–!!", "   "])
def test_slug_falls_back_to_the_id_when_nothing_is_left(name: str) -> None:
    assert location_slug(name, 7) == "location-7"
