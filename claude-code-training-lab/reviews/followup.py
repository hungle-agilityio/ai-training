from reviews.services import RATING_RANGES

STATUS_OPEN = "open"
STATUS_CONTACTED = "contacted"
STATUS_RESOLVED = "resolved"
# The order here is the order of every list of statuses.
STATUS_LABELS: dict[str, str] = {
    STATUS_OPEN: "Open",
    STATUS_CONTACTED: "Contacted",
    STATUS_RESOLVED: "Resolved",
}
NOTE_MAX_LENGTH = 500
STATUS_ERROR = "Choose a status from the list."
NOTE_ERROR = "Write a note of at most 500 characters."


def has_case(rating: int) -> bool:
    """Only a bad review has a follow-up case."""
    lowest, highest = RATING_RANGES["bad"]
    return lowest <= rating <= highest


def status_of(stored: str | None) -> str:
    """A case with nothing stored is open."""
    return stored or STATUS_OPEN


def followup_errors(status: str, note: str) -> list[str]:
    """Messages for a follow-up change that cannot be saved; empty when it is valid."""
    errors: list[str] = []
    if status not in STATUS_LABELS:
        errors.append(STATUS_ERROR)
    if len(note.strip()) > NOTE_MAX_LENGTH:
        errors.append(NOTE_ERROR)
    return errors
