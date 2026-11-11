from collections.abc import Iterable, Mapping

from reviews.location_names import clean_location_name, location_name_errors


class LocationForm:
    """Reads the name of a location; it is valid when the name rule gives no error."""

    def __init__(self, data: Mapping[str, str], taken_names: Iterable[str]) -> None:
        self.typed = data.get("name", "")
        self.name = clean_location_name(self.typed)
        self.errors = location_name_errors(self.typed, taken_names)

    def is_valid(self) -> bool:
        return not self.errors
