import pytest

from reviews.reply_service import REPLY_MAX_LENGTH, clean_reply_text


def test_reply_max_length_is_one_thousand() -> None:
    assert REPLY_MAX_LENGTH == 1000


def test_clean_reply_text_trims_spaces_and_line_breaks() -> None:
    assert clean_reply_text("  \n Thank you!\t\n") == "Thank you!"


@pytest.mark.parametrize("text", ["", "   ", "\n\t \r\n"])
def test_clean_reply_text_rejects_empty_text(text: str) -> None:
    assert clean_reply_text(text) is None


def test_clean_reply_text_allows_1000_characters() -> None:
    assert clean_reply_text("a" * 1000) == "a" * 1000


def test_clean_reply_text_rejects_1001_characters() -> None:
    assert clean_reply_text("a" * 1001) is None


def test_clean_reply_text_counts_after_trimming() -> None:
    assert clean_reply_text("  " + "a" * 1000 + "  ") == "a" * 1000
