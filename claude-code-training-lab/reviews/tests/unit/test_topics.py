import pytest

from reviews.management.commands.seed_demo_data import DEMO_REVIEWS
from reviews.topics import TOPICS, topic_by_slug, topics_of

EXPECTED: dict[str, list[str]] = {
    "Waited 50 minutes, nobody apologized.": ["Wait time"],
    "Front desk understaffed, queue out the door.": ["Wait time", "Staff"],
    "Doctor was great but check-in was slow.": ["Wait time", "Doctor & treatment"],
    "Billing mistake and nobody called back.": ["Price & billing", "Booking & phone"],
    "Friendly staff, quick visit.": ["Staff"],
    "Clean and efficient.": ["Cleanliness"],
    "Parking is expensive.": ["Price & billing", "Parking"],
    "Đau chân đỡ hẳn, nhân viên thân thiện": ["Staff", "Doctor & treatment"],
    "Dau dau khi cho doi": ["Wait time"],
    "Good care, parking is hard.": ["Doctor & treatment", "Parking"],
    "Best clinic experience I've had.": [],
    "Phone line always busy, could not book.": ["Booking & phone"],
    "Bác sĩ tận tâm, ĐAU LƯNG đã đỡ nhiều": ["Doctor & treatment"],
    "Nhân viên lễ tân chưa nhiệt tình": ["Staff"],
}


def test_topics_are_in_the_topic_order() -> None:
    slugs = [topic.slug for topic in TOPICS]
    assert slugs == ["wait", "staff", "care", "price", "booking", "parking", "cleanliness"]


def test_topic_by_slug_finds_and_ignores_unknown() -> None:
    assert topic_by_slug("staff") == TOPICS[1]
    assert topic_by_slug("nope") is None


@pytest.mark.parametrize(("text", "labels"), list(EXPECTED.items()))
def test_topics_of_demo_text(text: str, labels: list[str]) -> None:
    assert [topic.label for topic in topics_of(text)] == labels


def test_demo_texts_are_all_covered() -> None:
    demo = {text for items in DEMO_REVIEWS.values() for _, text in items}
    assert demo == set(EXPECTED)


def test_topics_of_ignores_case_and_matches_inside_a_word() -> None:
    assert [topic.slug for topic in topics_of("UNDERSTAFFED")] == ["staff"]


def test_topics_of_empty_text_is_empty() -> None:
    assert topics_of("") == ()
