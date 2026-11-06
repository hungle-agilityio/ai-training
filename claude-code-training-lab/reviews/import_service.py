import csv
import io
import re
from dataclasses import dataclass
from datetime import datetime

from reviews import import_repository
from reviews.import_repository import NewReview, ReviewKey
from reviews.services import CSV_FORMULA_STARTS, CSV_HEADER, VIETNAM_TZ

MAX_BYTES = 1_048_576
MAX_ROWS = 2_000
MAX_TEXT_LENGTH = 5_000
MAX_LOCATION_SHOWN = 60
DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d")

MSG_MISSING_COLUMNS = (
    "The file needs the columns Location, Rating, Review text and Date. Missing: {}."
)
MSG_NOT_UTF8 = "Save the file as CSV UTF-8 and try again."
MSG_TOO_LARGE = "The file is too large: at most 2,000 reviews and 1 MB."
MSG_NO_REVIEWS = "The file has no reviews."
MSG_RATING = "Rating must be a whole number from 1 to 5."
MSG_DATE = "Date must look like 2026-11-06 14:30 or 2026-11-06."
MSG_FUTURE = "Date is in the future."
MSG_LOCATION = 'Location "{}" was not found.'
MSG_TEXT_LONG = "Review text is longer than 5,000 characters."


@dataclass(frozen=True)
class ImportResult:
    imported: int
    duplicates: int
    errors: tuple[tuple[int, str], ...]
    refusal: str | None = None


@dataclass(frozen=True)
class _ParsedRow:
    number: int
    rating: int
    text: str
    created_at: datetime
    branch_id: int


def _refused(message: str) -> ImportResult:
    return ImportResult(imported=0, duplicates=0, errors=(), refusal=message)


def _unquote(value: str) -> str:
    """Undo the guard of `csv_safe`: one leading quote before a formula character."""
    if len(value) > 1 and value[0] == "'" and value[1] in CSV_FORMULA_STARTS:
        return value[1:]
    return value


def _parse_rating(cell: str) -> int | None:
    value = cell.strip()
    if value.isascii() and value.isdigit() and 1 <= int(value) <= 5:
        return int(value)
    return None


def _parse_date(cell: str) -> datetime | None:
    value = cell.strip()
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=VIETNAM_TZ)
        except ValueError:
            continue
    return None


def _column_positions(header: list[str]) -> dict[str, int]:
    wanted = {re.sub(r"\s+", " ", name).casefold(): name for name in CSV_HEADER}
    positions: dict[str, int] = {}
    for index, cell in enumerate(header):
        name = wanted.get(re.sub(r"\s+", " ", cell.strip()).casefold())
        if name is not None:
            positions.setdefault(name, index)
    return positions


def _cell(row: list[str], index: int) -> str:
    return row[index] if index < len(row) else ""


def import_reviews(data: bytes, *, now: datetime) -> ImportResult:
    """Check every row of a CSV file, skip duplicates and save the good rows in one go."""
    if len(data) > MAX_BYTES:
        return _refused(MSG_TOO_LARGE)
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _refused(MSG_NOT_UTF8)

    records = list(csv.reader(io.StringIO(content, newline="")))
    if not records:
        return _refused(MSG_NO_REVIEWS)
    positions = _column_positions(records[0])
    missing = [name for name in CSV_HEADER if name not in positions]
    if missing:
        return _refused(MSG_MISSING_COLUMNS.format(", ".join(missing)))

    body = [(number, row) for number, row in enumerate(records, start=1) if number > 1 and any(row)]
    if not body:
        return _refused(MSG_NO_REVIEWS)
    if len(body) > MAX_ROWS:
        return _refused(MSG_TOO_LARGE)

    location_ids = import_repository.location_ids_by_name()
    errors: list[tuple[int, str]] = []
    parsed: list[_ParsedRow] = []
    for number, row in body:
        rating = _parse_rating(_cell(row, positions["Rating"]))
        if rating is None:
            errors.append((number, MSG_RATING))
            continue
        created_at = _parse_date(_cell(row, positions["Date"]))
        if created_at is None:
            errors.append((number, MSG_DATE))
            continue
        if created_at > now:
            errors.append((number, MSG_FUTURE))
            continue
        location = _unquote(_cell(row, positions["Location"]).strip())
        branch_id = location_ids.get(location.casefold())
        if branch_id is None:
            errors.append((number, MSG_LOCATION.format(location[:MAX_LOCATION_SHOWN])))
            continue
        text = _unquote(_cell(row, positions["Review text"]).strip())
        if len(text) > MAX_TEXT_LENGTH:
            errors.append((number, MSG_TEXT_LONG))
            continue
        parsed.append(_ParsedRow(number, rating, text, created_at, branch_id))

    seen: set[ReviewKey] = set()
    if parsed:
        seen = import_repository.existing_keys(
            {item.branch_id for item in parsed},
            min(item.created_at for item in parsed),
            max(item.created_at for item in parsed),
        )
    to_save: list[NewReview] = []
    duplicates = 0
    for item in parsed:
        key = (item.branch_id, import_repository.minute_of(item.created_at), item.rating, item.text)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        to_save.append(NewReview(item.branch_id, item.rating, item.text, item.created_at))

    imported = import_repository.save_new_reviews(to_save) if to_save else 0
    return ImportResult(imported=imported, duplicates=duplicates, errors=tuple(errors))
