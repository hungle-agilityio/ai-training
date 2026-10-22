import csv
import io
from datetime import UTC, datetime

import pytest

from reviews.models import Branch, Business, Review
from reviews.services import ReviewFilters, csv_safe, export_filename, reviews_csv


def _branch(name: str = "Riverside") -> Branch:
    business, _ = Business.objects.get_or_create(name="Demo")
    return Branch.objects.create(business=business, name=name)


def _review(branch: Branch, rating: int, text: str, created_at: datetime) -> None:
    Review.objects.create(branch=branch, rating=rating, text=text, created_at=created_at)


def _rows(filters: ReviewFilters | None = None) -> list[list[str]]:
    content = "".join(reviews_csv(filters or ReviewFilters()))
    assert content.startswith("﻿")
    return list(csv.reader(io.StringIO(content.removeprefix("﻿"), newline="")))


@pytest.mark.parametrize("start", ["=", "+", "-", "@", "\t", "\r"])
def test_csv_safe_prefixes_a_quote_before_formula_characters(start: str) -> None:
    assert csv_safe(f"{start}1+1") == f"'{start}1+1"


def test_csv_safe_leaves_normal_text_alone() -> None:
    assert csv_safe("Friendly staff") == "Friendly staff"
    assert csv_safe("") == ""


def test_export_filename_uses_the_vietnam_date() -> None:
    # 17:30 UTC is already the next day in Vietnam
    assert export_filename(datetime(2026, 10, 21, 17, 30, tzinfo=UTC)) == "reviews-2026-10-22.csv"


@pytest.mark.django_db
def test_no_reviews_gives_only_the_header_with_the_utf8_marker() -> None:
    assert "".join(reviews_csv(ReviewFilters())) == "﻿Location,Rating,Review text,Date\r\n"


@pytest.mark.django_db
def test_rows_are_newest_first_with_full_text_and_vietnam_time() -> None:
    branch = _branch()
    long_text = "a" * 300
    _review(branch, 2, "older", datetime(2026, 10, 11, 17, 45, tzinfo=UTC))
    _review(branch, 4, long_text, datetime(2026, 10, 14, 2, 30, tzinfo=UTC))

    assert _rows() == [
        ["Location", "Rating", "Review text", "Date"],
        ["Riverside", "4", long_text, "2026-10-14 09:30"],
        ["Riverside", "2", "older", "2026-10-12 00:45"],
    ]


@pytest.mark.django_db
def test_reviews_written_at_the_same_minute_keep_a_fixed_order() -> None:
    branch = _branch()
    same = datetime(2026, 10, 14, 2, 30, tzinfo=UTC)
    for text in ("first", "second", "third"):
        _review(branch, 3, text, same)

    assert [row[2] for row in _rows()[1:]] == ["third", "second", "first"]
    assert _rows() == _rows()


@pytest.mark.django_db
def test_comma_quote_and_new_line_stay_in_one_cell() -> None:
    text = 'Great, "really"\nsecond line'
    _review(_branch(), 5, text, datetime(2026, 10, 14, 2, 30, tzinfo=UTC))

    assert _rows()[1][2] == text


@pytest.mark.django_db
def test_vietnamese_letters_are_kept() -> None:
    text = "Nhân viên rất nhiệt tình, đau chân đỡ hẳn"
    _review(_branch(), 5, text, datetime(2026, 10, 14, 2, 30, tzinfo=UTC))

    assert _rows()[1][2] == text


@pytest.mark.django_db
def test_formula_text_and_location_are_written_as_plain_text() -> None:
    _review(_branch("=Evil"), 1, '=HYPERLINK("http://example.com","Click")', datetime.now(UTC))

    row = _rows()[1]

    assert row[0] == "'=Evil"
    assert row[2] == '\'=HYPERLINK("http://example.com","Click")'


@pytest.mark.django_db
def test_filters_apply_together_and_a_wrong_value_is_ignored() -> None:
    riverside, airport = _branch("Riverside"), _branch("Airport")
    in_week = datetime(2026, 10, 14, 2, 30, tzinfo=UTC)
    _review(riverside, 1, "riverside-bad", in_week)
    _review(riverside, 5, "riverside-good", in_week)
    _review(airport, 1, "airport-bad", in_week)
    _review(riverside, 1, "riverside-old", datetime(2026, 10, 5, 2, 30, tzinfo=UTC))

    matching = ReviewFilters(branch_id=riverside.id, rating="bad", day=in_week.date())
    ignoring = ReviewFilters(branch_id=riverside.id, rating="nonsense", day=in_week.date())

    assert [row[2] for row in _rows(matching)[1:]] == ["riverside-bad"]
    assert sorted(row[2] for row in _rows(ignoring)[1:]) == ["riverside-bad", "riverside-good"]


@pytest.mark.django_db
def test_a_week_without_reviews_gives_only_the_header() -> None:
    branch = _branch()
    _review(branch, 4, "other week", datetime(2026, 10, 14, 2, 30, tzinfo=UTC))

    assert _rows(ReviewFilters(branch_id=branch.id, day=datetime(2026, 10, 5).date())) == [
        ["Location", "Rating", "Review text", "Date"]
    ]


@pytest.mark.django_db
def test_a_long_list_is_sent_in_several_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reviews.services.CSV_CHUNK_BYTES", 100)
    branch = _branch()
    for index in range(30):
        _review(branch, 3, f"review {index}", datetime(2026, 10, 14, 2, index, tzinfo=UTC))

    chunks = list(reviews_csv(ReviewFilters()))

    assert len(chunks) > 3
    assert len(_rows()) == 31
