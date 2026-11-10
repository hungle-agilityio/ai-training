import re

from reviews.services import RATING_RANGES

KIND_LABELS: dict[str, str] = {
    "good": "Good review (4–5 ★)",
    "bad": "Bad review (1–2 ★)",
    "any": "Any review",
}
LOCATION_PLACEHOLDER = "{location}"
NAME_MAX_LENGTH = 60
TEXT_MAX_LENGTH = 1000
NAME_ERROR = "Enter a name of 1 to 60 characters."
TEXT_ERROR = "Write a text of 1 to 1,000 characters."
PLACEHOLDER_PATTERN = re.compile(r"\{(\w+)\}")


def kinds_for_rating(rating: int) -> tuple[str, ...]:
    """A review gets the kinds whose rating range holds it, plus any."""
    fitting = tuple(
        kind
        for kind in ("good", "bad")
        if RATING_RANGES[kind][0] <= rating <= RATING_RANGES[kind][1]
    )
    return (*fitting, "any")


def fill_template(text: str, location_name: str) -> str:
    """Replace every placeholder in one pass, so the location name is never searched again."""
    return text.replace(LOCATION_PLACEHOLDER, location_name)


def template_errors(name: str, text: str) -> list[str]:
    """Messages for a template that cannot be saved; empty when it is valid."""
    errors: list[str] = []
    if not 1 <= len(name.strip()) <= NAME_MAX_LENGTH:
        errors.append(NAME_ERROR)
    if not 1 <= len(text.strip()) <= TEXT_MAX_LENGTH:
        errors.append(TEXT_ERROR)
    unknown = dict.fromkeys(
        word for word in PLACEHOLDER_PATTERN.findall(text) if word != "location"
    )
    for word in unknown:
        errors.append("Unknown placeholder {" + word + "}. You can use {location}.")
    return errors
