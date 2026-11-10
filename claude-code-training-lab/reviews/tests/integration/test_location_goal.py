import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.test import Client

from reviews.models import Branch, Business, Review


def _branch(goal: str | None, ratings: tuple[int, ...] = ()) -> Branch:
    business, _ = Business.objects.get_or_create(name="Demo")
    branch = Branch.objects.create(
        business=business, name="Clinic", target_score=Decimal(goal) if goal else None
    )
    for rating in ratings:
        Review.objects.create(
            branch=branch,
            rating=rating,
            text="t",
            created_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
    return branch


def _panel(branch: Branch) -> str:
    html = Client().get(f"/locations/{branch.pk}/").content.decode()
    match = re.search(r'<section class="panel" id="location-goal">.*?</section>', html, re.DOTALL)
    assert match, "goal panel missing"
    assert html.index("Score</h2>") < html.index('id="location-goal"')
    return re.sub(r"\s+", " ", match.group(0))


@pytest.mark.django_db
def test_goal_met_shows_positive_badge_and_change_link() -> None:
    panel = _panel(_branch("4.0", (5, 4)))
    assert "<h2>Goal</h2>" in panel
    assert "Target <strong>4.0</strong>" in panel
    assert 'badge-positive">Met<' in panel
    assert 'href="/settings/#settings-goals"' in panel
    assert "Change goal" in panel


@pytest.mark.django_db
def test_goal_short_shows_watch_badge() -> None:
    panel = _panel(_branch("4.5", (4, 4)))
    assert "Target <strong>4.5</strong>" in panel
    assert 'badge-watch">0.5 short<' in panel


@pytest.mark.django_db
def test_goal_without_reviews_says_no_score_yet() -> None:
    panel = _panel(_branch("4.5"))
    assert "Target <strong>4.5</strong>" in panel
    assert "No score yet" in panel


@pytest.mark.django_db
def test_no_goal_shows_set_a_goal_link() -> None:
    panel = _panel(_branch(None, (5,)))
    assert "No goal set." in panel
    assert "Set a goal" in panel
    assert 'href="/settings/#settings-goals"' in panel
