from django import template

from reviews.topics import Topic, topics_of

register = template.Library()


@register.filter
def review_topics(text: str) -> tuple[Topic, ...]:
    """The topics a review text mentions, in the topic order."""
    return topics_of(text)
