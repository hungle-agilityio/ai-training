from io import StringIO

import pytest
from django.core.management import call_command

from reviews.models import ReplyTemplate

EXPECTED = {
    "Thank you": (
        "good",
        "Thank you for your kind words! The team at {location} is glad you had a good visit, "
        "and we hope to see you again soon.",
    ),
    "We are sorry": (
        "bad",
        "We are sorry your visit to {location} did not go well. "
        "Please contact us so we can make it right.",
    ),
    "Thanks for the feedback": (
        "any",
        "Thank you for taking the time to share your feedback about {location}. "
        "It helps us improve.",
    ),
}


def seed() -> None:
    call_command("seed_demo_data", stdout=StringIO())


@pytest.mark.django_db
def test_seed_adds_the_three_demo_templates() -> None:
    seed()

    found = {t.name: (t.kind, t.text) for t in ReplyTemplate.objects.all()}
    assert found == EXPECTED


@pytest.mark.django_db
def test_seed_replaces_existing_templates() -> None:
    ReplyTemplate.objects.create(name="Old", text="old", kind="any")

    seed()
    seed()

    assert ReplyTemplate.objects.count() == len(EXPECTED)
    assert not ReplyTemplate.objects.filter(name="Old").exists()
