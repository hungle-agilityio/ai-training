import ast
from pathlib import Path

import pytest

from reviews import location_names
from reviews.location_names import (
    NAME_ERROR,
    NAME_MAX_LENGTH,
    TAKEN_ERROR,
    clean_location_name,
    location_name_errors,
)


def test_error_messages_are_the_agreed_texts() -> None:
    assert NAME_ERROR == "Enter a name of 1 to 120 characters."
    assert TAKEN_ERROR == "A location with this name already exists."
    assert NAME_MAX_LENGTH == 120


@pytest.mark.parametrize(
    ("text", "cleaned"),
    [
        ("Downtown", "Downtown"),
        ("  Downtown  ", "Downtown"),
        ("District   1    Clinic", "District 1 Clinic"),
        ("  District  1 ", "District 1"),
        ("\tDistrict\t 1\n", "District 1"),
        ("", ""),
        ("     ", ""),
    ],
)
def test_clean_trims_and_joins_runs_of_spaces(text: str, cleaned: str) -> None:
    assert clean_location_name(text) == cleaned


def test_clean_keeps_case_and_other_characters() -> None:
    assert clean_location_name(" Quận 1 <Spa> & Co ") == "Quận 1 <Spa> & Co"


def test_valid_name_has_no_errors() -> None:
    assert location_name_errors("Downtown", ["Uptown", "Riverside"]) == []


def test_valid_name_with_no_taken_names_has_no_errors() -> None:
    assert location_name_errors("Downtown", []) == []


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_empty_name_gives_the_length_error(name: str) -> None:
    assert location_name_errors(name, []) == [NAME_ERROR]


def test_name_of_one_character_is_valid() -> None:
    assert location_name_errors("A", []) == []


def test_name_of_120_characters_is_valid() -> None:
    assert location_name_errors("a" * 120, []) == []


def test_name_of_121_characters_gives_the_length_error() -> None:
    assert location_name_errors("a" * 121, []) == [NAME_ERROR]


def test_length_is_counted_on_the_cleaned_name() -> None:
    padded = "  " + "a" * 60 + "     " + "b" * 59 + "  "
    assert len(padded) > 120
    assert location_name_errors(padded, []) == []


def test_taken_name_gives_the_taken_error() -> None:
    assert location_name_errors("Downtown", ["Uptown", "Downtown"]) == [TAKEN_ERROR]


@pytest.mark.parametrize("name", ["downtown", "DOWNTOWN", "DownTown"])
def test_taken_name_is_matched_ignoring_case(name: str) -> None:
    assert location_name_errors(name, ["Downtown"]) == [TAKEN_ERROR]


def test_taken_name_is_matched_on_the_cleaned_name() -> None:
    assert location_name_errors("  District   1 ", ["district 1"]) == [TAKEN_ERROR]


def test_part_of_a_taken_name_is_not_taken() -> None:
    assert location_name_errors("Down", ["Downtown"]) == []


def test_taken_names_can_be_any_iterable() -> None:
    assert location_name_errors("Downtown", iter(["downtown"])) == [TAKEN_ERROR]


def test_errors_are_a_new_list_each_call() -> None:
    first = location_name_errors("Downtown", [])
    first.append("changed")
    assert location_name_errors("Downtown", []) == []


def test_rule_imports_no_django_and_no_model() -> None:
    tree = ast.parse(Path(location_names.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not [name for name in imported if name.startswith(("django", "reviews"))]
