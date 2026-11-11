from collections.abc import Iterable

NAME_MAX_LENGTH = 120
NAME_ERROR = "Enter a name of 1 to 120 characters."
TAKEN_ERROR = "A location with this name already exists."


def clean_location_name(text: str) -> str:
    """A location name has no spaces at its ends and one space between its words."""
    return " ".join(text.split())


def location_name_errors(name: str, taken_names: Iterable[str]) -> list[str]:
    """Messages for a location name that cannot be saved; empty when it is valid."""
    cleaned = clean_location_name(name)
    errors: list[str] = []
    if not 1 <= len(cleaned) <= NAME_MAX_LENGTH:
        errors.append(NAME_ERROR)
    if cleaned.casefold() in {taken.casefold() for taken in taken_names}:
        errors.append(TAKEN_ERROR)
    return errors
