import pytest

from reviews.reply_templates import (
    KIND_LABELS,
    NAME_ERROR,
    TEXT_ERROR,
    fill_template,
    kinds_for_rating,
    template_errors,
)


def test_kind_labels_are_the_agreed_texts() -> None:
    assert KIND_LABELS == {
        "good": "Good review (4–5 ★)",
        "bad": "Bad review (1–2 ★)",
        "any": "Any review",
    }


@pytest.mark.parametrize(
    ("rating", "kinds"),
    [
        (5, ("good", "any")),
        (4, ("good", "any")),
        (3, ("any",)),
        (2, ("bad", "any")),
        (1, ("bad", "any")),
    ],
)
def test_kinds_for_rating(rating: int, kinds: tuple[str, ...]) -> None:
    assert kinds_for_rating(rating) == kinds


def test_fill_replaces_every_placeholder() -> None:
    assert fill_template("Hi {location}, {location}!", "Hanoi") == "Hi Hanoi, Hanoi!"


def test_fill_without_placeholder_is_unchanged() -> None:
    assert fill_template("Thank you.", "Hanoi") == "Thank you."


def test_fill_does_not_replace_inside_the_location_name() -> None:
    assert fill_template("At {location}", "A {location} B") == "At A {location} B"


def test_valid_template_has_no_errors() -> None:
    assert template_errors("Thanks", "Thank you at {location}. { } ok") == []


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_bad_name_is_refused(name: str) -> None:
    assert template_errors(name, "text") == [NAME_ERROR]


def test_name_limits_are_inclusive_and_stripped() -> None:
    assert template_errors("  " + "x" * 60 + "  ", "text") == []


@pytest.mark.parametrize("text", ["", "  \n ", "x" * 1001])
def test_bad_text_is_refused(text: str) -> None:
    assert template_errors("name", text) == [TEXT_ERROR]


def test_text_limit_is_inclusive() -> None:
    assert template_errors("name", "x" * 1000) == []


def test_unknown_placeholders_listed_once_in_order() -> None:
    assert template_errors("n", "{b} {location} {a} {b}") == [
        "Unknown placeholder {b}. You can use {location}.",
        "Unknown placeholder {a}. You can use {location}.",
    ]


def test_all_errors_are_collected() -> None:
    assert template_errors("", "{x}") == [
        NAME_ERROR,
        "Unknown placeholder {x}. You can use {location}.",
    ]
