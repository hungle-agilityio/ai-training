from datetime import UTC, datetime

import pytest

from reviews import import_service
from reviews.import_service import ImportResult, import_reviews
from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

NOW = datetime(2026, 11, 6, 12, 0, tzinfo=UTC)
HEADER = "Location,Rating,Review text,Date\r\n"

pytestmark = pytest.mark.django_db


@pytest.fixture
def branch() -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="Riverside")


def _run(content: str | bytes, now: datetime = NOW) -> ImportResult:
    data = content.encode("utf-8") if isinstance(content, str) else content
    return import_reviews(data, now=now)


def test_good_row_is_imported_and_counts_are_ints(branch: Branch) -> None:
    result = _run(HEADER + "Riverside,5,Great,2026-11-05 14:30\r\n")

    assert (result.imported, result.duplicates, result.errors, result.refusal) == (1, 0, (), None)
    assert type(result.imported) is int and type(result.duplicates) is int
    review = Review.objects.get()
    assert (review.rating, review.text, review.branch_id) == (5, "Great", branch.pk)
    assert review.created_at == datetime(2026, 11, 5, 7, 30, tzinfo=UTC)
    assert review.search_text == "great"


def test_columns_in_any_order_with_other_columns_and_spaces(branch: Branch) -> None:
    content = " date ,extra, REVIEW TEXT,rating,location\n2026-11-05,x,Hi,3, riverside \n"

    result = _run(content)

    assert result.imported == 1
    assert Review.objects.get().created_at == datetime(2026, 11, 4, 17, 0, tzinfo=UTC)


def test_missing_columns_refuse_the_file(branch: Branch) -> None:
    result = _run("Location,Date\nRiverside,2026-11-05\n")

    assert result.refusal == (
        "The file needs the columns Location, Rating, Review text and Date. "
        "Missing: Rating, Review text."
    )
    assert Review.objects.count() == 0


def test_bom_is_accepted_and_vietnamese_text_kept(branch: Branch) -> None:
    result = _run("﻿" + HEADER + "Riverside,4,Dịch vụ tuyệt vời,2026-11-05\r\n")

    assert result.imported == 1
    assert Review.objects.get().text == "Dịch vụ tuyệt vời"


def test_not_utf8_refuses_the_file(branch: Branch) -> None:
    result = _run(b"Location,Rating,Review text,Date\n\xff\xfe\n")

    assert result.refusal == "Save the file as CSV UTF-8 and try again."


def test_too_many_rows_refuse_the_file(branch: Branch) -> None:
    rows = "Riverside,5,x,2026-11-05\n" * (import_service.MAX_ROWS + 1)

    assert _run(HEADER + rows).refusal == ("The file is too large: at most 2,000 reviews and 1 MB.")
    assert Review.objects.count() == 0


def test_too_many_bytes_refuse_the_file(branch: Branch) -> None:
    big = HEADER + "Riverside,5," + "a" * import_service.MAX_BYTES + ",2026-11-05\n"

    assert _run(big).refusal == "The file is too large: at most 2,000 reviews and 1 MB."


@pytest.mark.parametrize("content", ["", HEADER, HEADER + "\r\n,,,\r\n"])
def test_empty_or_header_only_has_no_reviews(content: str, branch: Branch) -> None:
    assert _run(content).refusal == "The file has no reviews."


def test_blank_lines_are_skipped_but_row_numbers_count_them(branch: Branch) -> None:
    result = _run(HEADER + "\r\n,,,\r\nRiverside,9,x,2026-11-05\r\n")

    assert result.errors == ((4, "Rating must be a whole number from 1 to 5."),)


@pytest.mark.parametrize("rating", ["0", "6", "x", "", "3.5", "-1", "+3"])
def test_bad_rating_is_a_row_error(rating: str, branch: Branch) -> None:
    result = _run(HEADER + f"Riverside,{rating},x,2026-11-05\n")

    assert result.errors == ((2, "Rating must be a whole number from 1 to 5."),)
    assert result.imported == 0


def test_rating_spaces_are_ignored(branch: Branch) -> None:
    assert _run(HEADER + "Riverside, 4 ,x,2026-11-05\n").imported == 1


@pytest.mark.parametrize("date", ["05/11/2026", "2026-13-01", "", "2026-11-05 14:30:15"])
def test_bad_date_is_a_row_error(date: str, branch: Branch) -> None:
    result = _run(HEADER + f"Riverside,5,x,{date}\n")

    assert result.errors == ((2, "Date must look like 2026-11-06 14:30 or 2026-11-06."),)


def test_future_date_is_a_row_error_and_now_is_not(branch: Branch) -> None:
    # NOW is 19:00 in Vietnam
    future = _run(HEADER + "Riverside,5,x,2026-11-06 19:01\n")
    same = _run(HEADER + "Riverside,5,x,2026-11-06 19:00\n")

    assert future.errors == ((2, "Date is in the future."),)
    assert same.imported == 1


def test_unknown_location_is_a_row_error_cut_to_60_characters(branch: Branch) -> None:
    result = _run(HEADER + f" {'L' * 80} ,5,x,2026-11-05\n")

    assert result.errors == ((2, f'Location "{"L" * 60}" was not found.'),)
    assert Branch.objects.count() == 1


def test_same_location_name_twice_uses_the_lowest_id(branch: Branch) -> None:
    other = Branch.objects.create(business=branch.business, name="RIVERSIDE")

    _run(HEADER + "riverside,5,x,2026-11-05\n")

    assert Review.objects.get().branch_id == min(branch.pk, other.pk)


def test_text_is_trimmed_and_may_be_empty(branch: Branch) -> None:
    result = _run(HEADER + 'Riverside,5,"  hi  ",2026-11-05\nRiverside,4,,2026-11-04\n')

    assert result.imported == 2
    assert sorted(Review.objects.values_list("text", flat=True)) == ["", "hi"]


@pytest.mark.parametrize("lead", ["=", "+", "-", "@", "\t", "\r"])
def test_formula_guard_quote_is_removed(lead: str, branch: Branch) -> None:
    _run(HEADER + f'Riverside,5,"\'{lead}x",2026-11-05\n')

    assert Review.objects.get().text == f"{lead}x"


def test_quote_before_a_normal_character_is_kept(branch: Branch) -> None:
    _run(HEADER + "Riverside,5,'ok,2026-11-05\n")

    assert Review.objects.get().text == "'ok"


def test_text_longer_than_5000_is_a_row_error_without_the_text(branch: Branch) -> None:
    secret = "s" * 5001
    result = _run(HEADER + f"Riverside,5,{secret},2026-11-05\n")

    assert result.errors == ((2, "Review text is longer than 5,000 characters."),)
    assert secret not in repr(result)


def test_text_of_exactly_5000_is_accepted(branch: Branch) -> None:
    assert _run(HEADER + f"Riverside,5,{'s' * 5000},2026-11-05\n").imported == 1


def test_only_the_first_problem_of_a_row_is_shown(branch: Branch) -> None:
    result = _run(HEADER + "Nowhere,9,x,bad\nNowhere,5,x,bad\nNowhere,5,x,2026-11-05\n")

    assert [message for _, message in result.errors] == [
        "Rating must be a whole number from 1 to 5.",
        "Date must look like 2026-11-06 14:30 or 2026-11-06.",
        'Location "Nowhere" was not found.',
    ]


def test_bad_rows_do_not_stop_good_rows(branch: Branch) -> None:
    result = _run(
        HEADER + "Riverside,5,a,2026-11-05\nRiverside,0,b,2026-11-05\nRiverside,4,c,2026-11-05\n"
    )

    assert (result.imported, len(result.errors)) == (2, 1)
    assert result.errors[0][0] == 3


def test_existing_review_is_a_duplicate_to_the_minute(branch: Branch) -> None:
    create_review(
        branch=branch,
        rating=5,
        text="Great",
        created_at=datetime(2026, 11, 5, 7, 30, 45, tzinfo=UTC),
    )

    result = _run(HEADER + "Riverside,5,Great,2026-11-05 14:30\n")

    assert (result.imported, result.duplicates, result.errors) == (0, 1, ())
    assert Review.objects.count() == 1


def test_same_row_twice_in_one_file_is_one_import_and_one_duplicate(branch: Branch) -> None:
    row = "Riverside,5,Great,2026-11-05 14:30\n"

    result = _run(HEADER + row + row)

    assert (result.imported, result.duplicates) == (1, 1)


def test_other_rating_or_minute_is_not_a_duplicate(branch: Branch) -> None:
    rows = "Riverside,5,Great,2026-11-05 14:30\nRiverside,4,Great,2026-11-05 14:30\n"
    rows += "Riverside,5,Great,2026-11-05 14:31\n"

    assert _run(HEADER + rows).imported == 3


def test_importing_the_same_file_twice_adds_nothing(branch: Branch) -> None:
    content = HEADER + "Riverside,5,Great,2026-11-05 14:30\n"

    _run(content)
    second = _run(content)

    assert (second.imported, second.duplicates) == (0, 1)
    assert Review.objects.count() == 1
