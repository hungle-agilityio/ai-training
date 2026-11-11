import ast
from pathlib import Path

import pytest

from reviews import followup
from reviews.followup import (
    NOTE_ERROR,
    NOTE_MAX_LENGTH,
    STATUS_CONTACTED,
    STATUS_ERROR,
    STATUS_LABELS,
    STATUS_OPEN,
    STATUS_RESOLVED,
    followup_errors,
    has_case,
    status_of,
)
from reviews.services import RATING_RANGES


def test_statuses_are_open_contacted_resolved_in_that_order() -> None:
    assert (STATUS_OPEN, STATUS_CONTACTED, STATUS_RESOLVED) == ("open", "contacted", "resolved")
    assert list(STATUS_LABELS.items()) == [
        ("open", "Open"),
        ("contacted", "Contacted"),
        ("resolved", "Resolved"),
    ]


@pytest.mark.parametrize(
    ("rating", "expected"),
    [(1, True), (2, True), (3, False), (4, False), (5, False)],
)
def test_only_a_bad_review_has_a_case(rating: int, expected: bool) -> None:
    assert has_case(rating) is expected


def test_has_case_follows_the_bad_range_of_the_rating_ranges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(RATING_RANGES, "bad", (1, 3))

    assert has_case(3) is True
    assert has_case(4) is False


def test_status_is_open_when_nothing_is_stored() -> None:
    assert status_of(None) == "open"


@pytest.mark.parametrize("stored", ["open", "contacted", "resolved"])
def test_status_is_the_stored_one(stored: str) -> None:
    assert status_of(stored) == stored


@pytest.mark.parametrize("status", ["open", "contacted", "resolved"])
def test_a_known_status_with_an_empty_note_is_valid(status: str) -> None:
    assert followup_errors(status, "") == []


@pytest.mark.parametrize("status", ["", "closed", "Open", " open", "OPEN"])
def test_an_unknown_status_gives_the_status_message(status: str) -> None:
    assert followup_errors(status, "Called back.") == ["Choose a status from the list."]
    assert STATUS_ERROR == "Choose a status from the list."


def test_a_note_of_500_characters_is_valid() -> None:
    assert NOTE_MAX_LENGTH == 500
    assert followup_errors("contacted", "a" * 500) == []


def test_a_note_of_501_characters_gives_the_note_message() -> None:
    assert followup_errors("contacted", "a" * 501) == ["Write a note of at most 500 characters."]
    assert NOTE_ERROR == "Write a note of at most 500 characters."


def test_the_note_length_is_counted_after_stripping() -> None:
    assert followup_errors("resolved", "  " + "a" * 500 + "\n\n") == []
    assert followup_errors("resolved", "   ") == []


def test_an_unknown_status_and_a_long_note_give_both_messages_status_first() -> None:
    assert followup_errors("closed", "a" * 501) == [
        "Choose a status from the list.",
        "Write a note of at most 500 characters.",
    ]


def test_the_rule_imports_no_model_and_no_database() -> None:
    tree = ast.parse(Path(followup.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert imported == ["reviews.services"]
