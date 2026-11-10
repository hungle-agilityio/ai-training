from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client

from reviews.models import Branch, Business

pytestmark = pytest.mark.login

ERROR = "Enter a score from 1.0 to 5.0 with one decimal."


@pytest.fixture
def client(db: None) -> Client:
    user: User = get_user_model().objects.create_user(username="demo", password="pw-long-enough-1")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def two_locations(db: None) -> tuple[Branch, Branch]:
    business = Business.objects.create(name="Clinics")
    return (
        Branch.objects.create(business=business, name="Beta Spa", target_score=Decimal("4.0")),
        Branch.objects.create(business=business, name="Alpha Clinic"),
    )


def test_panel_lists_locations_by_name_between_account_and_suggestions(
    client: Client, two_locations: tuple[Branch, Branch]
) -> None:
    page = client.get("/settings/").content.decode()
    assert 'id="settings-goals"' in page
    assert "Location goals" in page
    assert "Target score from 1.0 to 5.0. Leave empty for no goal." in page
    assert page.index("settings-account") < page.index("settings-goals")
    assert page.index("settings-goals") < page.index("settings-suggestions")
    beta, alpha = two_locations[0], two_locations[1]
    assert page.index(f"goal-{alpha.pk}") < page.index(f"goal-{beta.pk}")
    assert 'step="0.1"' in page and 'min="1.0"' in page and 'max="5.0"' in page
    assert 'value="4.0"' in page
    assert "Save goals" in page


def test_panel_without_locations_has_no_button(client: Client) -> None:
    page = client.get("/settings/").content.decode()
    assert "No locations yet." in page
    assert "Save goals" not in page


def test_get_redirects_to_settings(client: Client) -> None:
    response = client.get("/settings/goals/")
    assert response.status_code == 302
    assert response["Location"] == "/settings/"


def test_valid_post_saves_clears_and_shows_notice_once(
    client: Client, two_locations: tuple[Branch, Branch]
) -> None:
    beta, alpha = two_locations[0], two_locations[1]
    response = client.post("/settings/goals/", {f"goal-{beta.pk}": "", f"goal-{alpha.pk}": "4.5"})
    assert response.status_code == 302
    assert response["Location"] == "/settings/?goals=saved"
    beta.refresh_from_db()
    alpha.refresh_from_db()
    assert beta.target_score is None
    assert alpha.target_score == Decimal("4.5")
    page = client.get("/settings/?goals=saved").content.decode()
    assert 'id="goals-saved"' in page and "Goals saved." in page
    assert 'id="goals-saved"' not in client.get("/settings/").content.decode()


@pytest.mark.parametrize("bad", ["0.9", "5.1", "4.25", "abc"])
def test_invalid_value_saves_nothing_and_keeps_input(
    client: Client, two_locations: tuple[Branch, Branch], bad: str
) -> None:
    beta, alpha = two_locations[0], two_locations[1]
    response = client.post("/settings/goals/", {f"goal-{beta.pk}": "2.0", f"goal-{alpha.pk}": bad})
    page = response.content.decode()
    assert response.status_code == 200
    assert ERROR in page
    assert f'value="{bad}"' in page
    assert f'aria-describedby="goal-{alpha.pk}-error"' in page
    beta.refresh_from_db()
    assert beta.target_score == Decimal("4.0")


def test_unknown_location_is_ignored(client: Client, two_locations: tuple[Branch, Branch]) -> None:
    response = client.post("/settings/goals/", {"goal-999999": "3.0", "goal-x": "1.0"})
    assert response.status_code == 302


def test_sign_in_needed(db: None) -> None:
    response = Client().post("/settings/goals/", {})
    assert response.status_code == 302
    assert response["Location"].startswith("/login/")
