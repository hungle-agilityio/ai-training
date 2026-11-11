from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review

pytestmark = pytest.mark.login

NOW = datetime(2026, 11, 1, tzinfo=UTC)
NAME_ERROR = "Enter a name of 1 to 120 characters."
TAKEN_ERROR = "A location with this name already exists."
RENAMED_URL = "/settings/?locations=renamed#settings-locations"


@pytest.fixture
def client(db: None) -> Client:
    user = get_user_model().objects.create_user(username="demo", password="correct-horse-battery")
    client = Client()
    client.force_login(user)
    return client


def make(*names: str) -> list[Branch]:
    business = Business.objects.create(name="Demo")
    return [Branch.objects.create(business=business, name=name) for name in names]


def rename_url(branch: Branch) -> str:
    return f"/settings/locations/{branch.id}/"


def test_page_shows_the_form_filled_with_the_current_name(client: Client) -> None:
    (downtown,) = make("Downtown")
    response = client.get(rename_url(downtown))
    html = response.content.decode()
    assert response.status_code == 200
    assert "reviews/location_rename.html" in [t.name for t in response.templates]
    assert "Rename location" in html
    assert f'<form class="settings-form" method="post" action="{rename_url(downtown)}">' in html
    assert "csrfmiddlewaretoken" in html
    assert '<label for="location-name">Name</label>' in html
    assert (
        '<input type="text" id="location-name" name="name" maxlength="120" value="Downtown">'
        in html
    )
    assert "Save name</button>" in html
    assert 'href="/settings/#settings-locations"' in html
    assert ">Cancel</a>" in html
    assert "aria-describedby" not in html


def test_unknown_id_is_404(client: Client) -> None:
    assert client.get("/settings/locations/999/").status_code == 404
    assert client.post("/settings/locations/999/", {"name": "Downtown"}).status_code == 404


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_other_methods_are_405(client: Client, method: str) -> None:
    (downtown,) = make("Downtown")
    assert getattr(client, method)(rename_url(downtown)).status_code == 405


def test_visitor_is_sent_to_sign_in_and_renames_nothing(db: None) -> None:
    (downtown,) = make("Downtown")
    url = rename_url(downtown)
    for response in (Client().get(url), Client().post(url, {"name": "Uptown"})):
        assert response.status_code == 302
        assert response["Location"] == f"/login/?next={url}"
    downtown.refresh_from_db()
    assert downtown.name == "Downtown"


def test_post_without_csrf_token_is_403(client: Client) -> None:
    (downtown,) = make("Downtown")
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(get_user_model().objects.get(username="demo"))
    assert strict.post(rename_url(downtown), {"name": "Uptown"}).status_code == 403
    downtown.refresh_from_db()
    assert downtown.name == "Downtown"


def test_valid_post_saves_the_cleaned_name_and_redirects_to_the_panel(client: Client) -> None:
    airport, downtown = make("Airport", "Downtown")
    response = client.post(rename_url(downtown), {"name": "  Old   town  "})
    assert response.status_code == 302
    assert response["Location"] == RENAMED_URL
    downtown.refresh_from_db()
    airport.refresh_from_db()
    assert (airport.name, downtown.name) == ("Airport", "Old town")
    assert Branch.objects.count() == 2


def test_renamed_notice_shows_only_for_renamed(client: Client) -> None:
    html = client.get("/settings/?locations=renamed").content.decode()
    assert '<p class="notice" id="locations-saved" role="status">Location renamed.</p>' in html
    assert "Location added." not in html
    for value in ("", "1", "saved", "Renamed", "added"):
        other = client.get("/settings/?locations=" + value).content.decode()
        assert "Location renamed." not in other


def test_own_name_does_not_count_as_taken(client: Client) -> None:
    _, downtown = make("Airport", "Downtown")
    response = client.post(rename_url(downtown), {"name": "DOWNTOWN"})
    assert response.status_code == 302
    assert response["Location"] == RENAMED_URL
    downtown.refresh_from_db()
    assert downtown.name == "DOWNTOWN"


@pytest.mark.parametrize(
    ("typed", "error"),
    [
        ("", NAME_ERROR),
        ("   ", NAME_ERROR),
        ("x" * 121, NAME_ERROR),
        ("airport", TAKEN_ERROR),
        ("  AIR   PORT ", TAKEN_ERROR),
    ],
)
def test_invalid_post_saves_nothing_and_shows_the_rename_page_with_the_error(
    client: Client, typed: str, error: str
) -> None:
    _, _, downtown = make("Airport", "Air Port", "Downtown")
    response = client.post(rename_url(downtown), {"name": typed})
    html = response.content.decode()
    assert response.status_code == 200
    assert "reviews/location_rename.html" in [t.name for t in response.templates]
    assert "Rename location" in html
    assert f'name="name" maxlength="120" value="{typed}"' in html
    assert f'<p class="settings-error">{error}</p>' in html
    assert 'aria-describedby="location-name-error" aria-invalid="true"' in html
    assert html.index('id="location-name"') < html.index('id="location-name-error"')
    assert sorted(Branch.objects.values_list("name", flat=True)) == [
        "Air Port",
        "Airport",
        "Downtown",
    ]


def test_post_without_a_name_field_is_refused(client: Client) -> None:
    (downtown,) = make("Downtown")
    response = client.post(rename_url(downtown), {})
    assert response.status_code == 200
    assert NAME_ERROR in response.content.decode()
    downtown.refresh_from_db()
    assert downtown.name == "Downtown"


def test_a_name_with_markup_is_escaped(client: Client) -> None:
    (branch,) = make("<b>Tom & Co</b>")
    html = client.get(rename_url(branch)).content.decode()
    assert "<b>Tom" not in html
    assert 'value="&lt;b&gt;Tom &amp; Co&lt;/b&gt;"' in html


def test_rename_keeps_reviews_goal_and_score(client: Client) -> None:
    (downtown,) = make("Downtown")
    Branch.objects.filter(id=downtown.id).update(target_score=Decimal("4.5"))
    for rating in (5, 4, 4):
        Review.objects.create(branch=downtown, rating=rating, text="ok", created_at=NOW)
    review_ids = sorted(Review.objects.values_list("id", flat=True))
    before = client.get("/dashboard/").content.decode()
    assert "4.3" in before

    assert client.post(rename_url(downtown), {"name": "Old town"}).status_code == 302

    downtown.refresh_from_db()
    assert downtown.name == "Old town"
    assert downtown.target_score == Decimal("4.5")
    assert sorted(Review.objects.filter(branch=downtown).values_list("id", flat=True)) == review_ids
    after = client.get("/dashboard/").content.decode()
    assert "Old town" in after
    assert "Downtown" not in after
    assert "4.3" in after
    assert 'value="4.5"' in client.get("/settings/").content.decode()


def test_get_makes_at_most_three_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    branches = make(*[f"Location {index:03d}" for index in range(200)])
    with django_assert_max_num_queries(3):
        assert client.get(rename_url(branches[0])).status_code == 200


def test_posts_make_at_most_five_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    branches = make(*[f"Location {index:03d}" for index in range(200)])
    with django_assert_max_num_queries(5):
        assert client.post(rename_url(branches[0]), {"name": "Newtown"}).status_code == 302
    with django_assert_max_num_queries(5):
        assert client.post(rename_url(branches[1]), {"name": "newtown"}).status_code == 200
