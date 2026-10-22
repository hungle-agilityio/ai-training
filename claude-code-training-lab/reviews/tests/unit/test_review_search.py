import csv
import io
import unicodedata
from datetime import UTC, datetime, timedelta

import pytest

from reviews.forms import ReviewFilterForm
from reviews.models import Branch, Business
from reviews.repositories import create_review
from reviews.search_text import SEARCH_MAX_LENGTH
from reviews.services import ReviewFilters, reviews_csv, reviews_page

pytestmark = pytest.mark.django_db

BASE = datetime(2026, 10, 14, 2, 0, tzinfo=UTC)  # Wednesday of week 12 to 18 October 2026


def _branches() -> tuple[Branch, Branch]:
    business = Business.objects.create(name="Demo")
    return (
        Branch.objects.create(business=business, name="Airport"),
        Branch.objects.create(business=business, name="Riverside"),
    )


def _add(branch: Branch, rating: int, text: str, minutes: int = 0, days: int = 0) -> None:
    create_review(
        branch=branch,
        rating=rating,
        text=text,
        created_at=BASE + timedelta(minutes=minutes, days=days),
    )


def _texts(search: str, **filters: object) -> list[str]:
    page = reviews_page(None, 100, ReviewFilters(search=search, **filters))  # type: ignore[arg-type]
    return [row.text for row in page.rows]


def _form_filters(data: dict[str, str]) -> ReviewFilters:
    return ReviewFilterForm(data).filters()


@pytest.fixture
def parking() -> tuple[Branch, Branch]:
    airport, riverside = _branches()
    _add(riverside, 2, "No parking nearby", minutes=1)
    _add(airport, 5, "Easy parking, friendly staff", minutes=2)
    _add(riverside, 3, "Parking was full", minutes=3)
    _add(airport, 4, "Quick visit")
    return airport, riverside


def test_one_word_shows_matching_reviews_newest_first(parking: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, 20, ReviewFilters(search="parking"))

    assert [row.text for row in page.rows] == [
        "Parking was full",
        "Easy parking, friendly staff",
        "No parking nearby",
    ]
    assert page.total == 3
    assert isinstance(page.total, int)
    assert page.is_filtered is True


def test_capital_letters_are_the_same_as_small_letters(parking: tuple[Branch, Branch]) -> None:
    assert _texts("PARKING") == _texts("parking")
    assert len(_texts("PARKING")) == 3


def test_accented_capital_letters_are_found() -> None:
    airport, _ = _branches()
    _add(airport, 5, "Đau chân đỡ hẳn, nhân viên thân thiện")

    assert _texts("ĐAU CHÂN") == ["Đau chân đỡ hẳn, nhân viên thân thiện"]
    assert len(_texts("NHÂN")) == 1


def test_a_search_without_accents_does_not_find_accented_text() -> None:
    airport, _ = _branches()
    _add(airport, 5, "Đau chân đỡ hẳn, nhân viên thân thiện", minutes=1)
    _add(airport, 3, "Dau dau khi cho doi", minutes=2)

    assert _texts("dau") == ["Dau dau khi cho doi"]


def test_nfd_search_finds_nfc_text_and_back() -> None:
    airport, _ = _branches()
    nfc = unicodedata.normalize("NFC", "Nhân viên thân thiện")
    nfd = unicodedata.normalize("NFD", "Đau chân đỡ hẳn")
    _add(airport, 5, nfc, minutes=1)
    _add(airport, 4, nfd, minutes=2)

    assert _texts(unicodedata.normalize("NFD", "NHÂN VIÊN")) == [nfc]
    assert _texts(unicodedata.normalize("NFC", "đau chân")) == [nfd]


def test_every_word_must_appear_in_any_order(parking: tuple[Branch, Branch]) -> None:
    assert _texts("parking full") == ["Parking was full"]
    assert _texts("full parking") == ["Parking was full"]
    assert _texts("parking elevator") == []


def test_part_of_a_word_matches(parking: tuple[Branch, Branch]) -> None:
    assert len(_texts("park")) == 3
    assert len(_texts("rkin")) == 3


def test_search_combines_with_location_rating_and_week(parking: tuple[Branch, Branch]) -> None:
    airport, riverside = parking
    _add(riverside, 5, "Parking is great", minutes=4, days=14)

    assert _texts("parking", branch_id=riverside.id) == [
        "Parking is great",
        "Parking was full",
        "No parking nearby",
    ]
    assert _texts("parking", branch_id=riverside.id, rating="bad") == ["No parking nearby"]
    assert _texts("parking", day=BASE.date()) == [
        "Parking was full",
        "Easy parking, friendly staff",
        "No parking nearby",
    ]
    assert _texts("parking", branch_id=airport.id, rating="good", day=BASE.date()) == [
        "Easy parking, friendly staff"
    ]


def test_page_links_keep_the_search(parking: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, 2, ReviewFilters(search="parking"))

    assert page.next_href == "?search=parking&page=2"
    assert page.previous_href == "?search=parking&page=1"
    assert page.links[1].href == "?search=parking&page=2"
    assert page.query_params == [("search", "parking")]


@pytest.mark.parametrize("raw", ["", "   "])
def test_blank_search_does_not_filter_or_warn(raw: str, parking: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, 20, _form_filters({"search": raw}))

    assert page.total == 4
    assert page.search_too_short is False
    assert page.is_filtered is False
    assert page.show_clear is False
    assert page.query_params == []


@pytest.mark.parametrize("raw", ["pa", " pa "])
def test_too_short_search_warns_and_does_not_filter(
    raw: str, parking: tuple[Branch, Branch]
) -> None:
    _, riverside = parking

    page = reviews_page(None, 20, _form_filters({"search": raw, "location": str(riverside.id)}))

    assert page.search_too_short is True
    assert page.search_value == "pa"
    assert page.total == 2  # both Riverside reviews, the search is not used
    assert ("search", "pa") not in page.query_params
    assert page.query_params == [("location", str(riverside.id))]
    assert page.export_query == f"location={riverside.id}"
    assert page.show_clear is True
    assert page.is_filtered is True


def test_a_space_inside_counts_as_a_character(parking: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, 20, _form_filters({"search": "an to"}))

    assert page.search_too_short is False
    assert page.total == 0


def test_percent_and_underscore_are_plain_text() -> None:
    airport, _ = _branches()
    _add(airport, 5, "100% happy", minutes=1)
    _add(airport, 3, "1000 reasons", minutes=2)
    _add(airport, 3, "a_b test text", minutes=3)
    _add(airport, 3, "axb test text", minutes=4)

    assert _texts("100%") == ["100% happy"]
    assert _texts("a_b") == ["a_b test text"]


def test_form_cuts_a_long_search_to_100_characters_without_an_error() -> None:
    form = ReviewFilterForm({"search": "a" * 150})

    assert form.is_valid()
    assert form.filters().search == "a" * SEARCH_MAX_LENGTH


def test_null_character_is_ignored_and_other_filters_still_apply() -> None:
    form = ReviewFilterForm({"search": "park\x00ing", "rating": "bad"})

    filters = form.filters()

    assert filters.search == ""
    assert filters.rating == "bad"


def test_export_link_carries_the_search(parking: tuple[Branch, Branch]) -> None:
    page = reviews_page(None, 20, ReviewFilters(search="parking"))

    assert page.export_query == "search=parking"


def test_csv_follows_the_search(parking: tuple[Branch, Branch]) -> None:
    content = "".join(reviews_csv(ReviewFilters(search="parking full"))).removeprefix("﻿")

    rows = list(csv.reader(io.StringIO(content, newline="")))

    assert [row[2] for row in rows[1:]] == ["Parking was full"]
