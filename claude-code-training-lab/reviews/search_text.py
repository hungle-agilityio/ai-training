import re
import unicodedata

SEARCH_MAX_LENGTH = 100


def normalize_for_search(text: str) -> str:
    """One searchable form: one Unicode form and no difference between capital and small letters."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFC", text).casefold())


def tidy_search_input(raw: str) -> str:
    """A typed search: one space between words, one Unicode form, at most 100 characters."""
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFC", raw)).strip()
    return text[:SEARCH_MAX_LENGTH].strip()
