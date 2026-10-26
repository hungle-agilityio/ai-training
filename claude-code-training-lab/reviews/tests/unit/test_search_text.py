import unicodedata

from reviews.search_text import SEARCH_MAX_LENGTH, normalize_for_search, tidy_search_input


def test_case_is_ignored_for_accented_letters() -> None:
    assert normalize_for_search("ĐAU CHÂN") == normalize_for_search("Đau chân")
    assert normalize_for_search("NHÂN") == normalize_for_search("nhân")


def test_nfd_and_nfc_give_the_same_text() -> None:
    nfc = unicodedata.normalize("NFC", "Đau chân")
    nfd = unicodedata.normalize("NFD", "Đau chân")

    assert nfc != nfd
    assert normalize_for_search(nfd) == normalize_for_search(nfc)


def test_accents_still_count() -> None:
    assert normalize_for_search("dau") != normalize_for_search("đau")


def test_tidy_trims_and_collapses_spaces() -> None:
    assert tidy_search_input("  parking \t  full\n ") == "parking full"


def test_tidy_cuts_to_100_characters() -> None:
    result = tidy_search_input("a" * 99 + " " + "b" * 50)

    assert SEARCH_MAX_LENGTH == 100
    assert result == "a" * 99
    assert len(tidy_search_input("a" * 150)) == 100


def test_tidy_counts_nfd_letters_once() -> None:
    nfd = unicodedata.normalize("NFD", "â" * 100)

    assert len(nfd) == 200
    assert tidy_search_input(nfd) == "â" * 100
