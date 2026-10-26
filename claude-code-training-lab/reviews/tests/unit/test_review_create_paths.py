import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2]
SKIPPED_FOLDERS = {"tests", "migrations"}
FORBIDDEN = re.compile(r"Review\.objects\.create|bulk_create|(?<!class )\bReview\(")


def test_reviews_are_created_only_through_the_repository() -> None:
    offenders = [
        str(path.relative_to(APP_DIR))
        for path in APP_DIR.rglob("*.py")
        if not SKIPPED_FOLDERS & set(path.relative_to(APP_DIR).parts)
        and path.name != "repositories.py"
        and FORBIDDEN.search(path.read_text())
    ]

    assert offenders == []
