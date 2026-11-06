from dataclasses import dataclass

from reviews.search_text import normalize_for_search


@dataclass(frozen=True)
class Topic:
    slug: str
    label: str
    keywords: tuple[str, ...]


TOPICS: tuple[Topic, ...] = (
    Topic("wait", "Wait time", ("wait", "queue", "slow", "delay", "chờ", "cho doi", "đợi")),
    Topic(
        "staff",
        "Staff",
        ("staff", "front desk", "reception", "nurse", "nhân viên", "lễ tân"),
    ),
    Topic(
        "care",
        "Doctor & treatment",
        ("doctor", "care", "treatment", "bác sĩ", "điều trị", "đau"),
    ),
    Topic(
        "price",
        "Price & billing",
        ("price", "expensive", "bill", "charge", "cost", "giá", "đắt"),
    ),
    Topic(
        "booking",
        "Booking & phone",
        ("book", "appointment", "phone", "call", "đặt lịch", "điện thoại", "gọi"),
    ),
    Topic("parking", "Parking", ("parking", "car park", "gửi xe", "đỗ xe")),
    Topic("cleanliness", "Cleanliness", ("clean", "dirty", "hygiene", "smell", "sạch", "bẩn")),
)


def topic_by_slug(slug: str) -> Topic | None:
    return next((topic for topic in TOPICS if topic.slug == slug), None)


def normalized_keywords(topic: Topic) -> tuple[str, ...]:
    return tuple(normalize_for_search(keyword) for keyword in topic.keywords)


def topics_of(text: str) -> tuple[Topic, ...]:
    """The topics a text mentions, in the topic order; a keyword inside a longer word counts."""
    searchable = normalize_for_search(text)
    return tuple(
        topic
        for topic in TOPICS
        if any(keyword in searchable for keyword in normalized_keywords(topic))
    )
