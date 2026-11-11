import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business

pytestmark = pytest.mark.login

URL = "/settings/locations/"
NAME_ERROR = "Enter a name of 1 to 120 characters."
TAKEN_ERROR = "A location with this name already exists."


@pytest.fixture
def client(db: None) -> Client:
    user = get_user_model().objects.create_user(username="demo", password="correct-horse-battery")
    client = Client()
    client.force_login(user)
    return client


def make(*names: str) -> list[Branch]:
    business = Business.objects.create(name="Demo")
    return [Branch.objects.create(business=business, name=name) for name in names]


def panel(html: str) -> str:
    start = html.index('id="settings-locations"')
    return html[start : html.index("</section>", start)]


def test_panel_sits_between_account_and_goals_with_its_title(client: Client) -> None:
    html = client.get("/settings/").content.decode()
    assert '<section class="panel settings-panel" id="settings-locations">' in html
    assert html.index('id="settings-account"') < html.index('id="settings-locations"')
    assert html.index('id="settings-locations"') < html.index('id="settings-goals"')
    assert "<h2>Locations</h2>" in panel(html)


def test_empty_panel_says_to_add_the_first_location(client: Client) -> None:
    html = panel(client.get("/settings/").content.decode())
    assert "No locations yet. Add your first one below." in html
    assert "Rename" not in html


def test_rows_are_ordered_by_name_then_id_with_a_rename_link(client: Client) -> None:
    riverside, first_airport, second_airport = make("Riverside", "Airport", "Airport")
    html = panel(client.get("/settings/").content.decode())
    links = re.findall(r'<a href="([^"]+)" aria-label="([^"]+)">Rename</a>', html)
    assert links == [
        (f"/settings/locations/{first_airport.id}/", "Rename Airport"),
        (f"/settings/locations/{second_airport.id}/", "Rename Airport"),
        (f"/settings/locations/{riverside.id}/", "Rename Riverside"),
    ]
    assert html.index("Airport") < html.index("Riverside")
    assert "No locations yet. Add your first one below." not in html


def test_add_form_has_a_name_field_and_a_button(client: Client) -> None:
    html = panel(client.get("/settings/").content.decode())
    assert "Add a location" in html
    assert (
        f'<form class="settings-form settings-locations-form" method="post" action="{URL}">' in html
    )
    assert "csrfmiddlewaretoken" in html
    assert '<label for="location-name">Name</label>' in html
    assert '<input type="text" id="location-name" name="name" maxlength="120" value="">' in html
    assert "Add location</button>" in html
    assert "aria-describedby" not in html
    assert 'id="locations-saved"' not in html


def test_get_redirects_to_settings(client: Client) -> None:
    response = client.get(URL)
    assert response.status_code == 302
    assert response["Location"] == "/settings/"


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_other_methods_are_405(client: Client, method: str) -> None:
    assert getattr(client, method)(URL).status_code == 405


def test_valid_post_adds_the_cleaned_name_and_redirects_to_the_panel(client: Client) -> None:
    make("Airport")
    response = client.post(URL, {"name": "  New   town  "})
    assert response.status_code == 302
    assert response["Location"] == "/settings/?locations=added#settings-locations"
    assert sorted(Branch.objects.values_list("name", flat=True)) == ["Airport", "New town"]
    assert Business.objects.count() == 1


def test_first_location_creates_my_business(client: Client) -> None:
    response = client.post(URL, {"name": "Downtown"})
    assert response.status_code == 302
    branch = Branch.objects.select_related("business").get()
    assert branch.name == "Downtown"
    assert branch.business.name == "My business"


def test_added_notice_shows_only_for_added(client: Client) -> None:
    html = client.get("/settings/?locations=added").content.decode()
    assert '<p class="notice" id="locations-saved" role="status">Location added.</p>' in html
    for value in ("", "1", "saved", "Added"):
        other = client.get("/settings/?locations=" + value).content.decode()
        assert "locations-saved" not in other
        assert "Location added." not in other


def test_new_location_shows_on_the_other_pages_with_no_score(client: Client) -> None:
    make("Airport")
    client.post(URL, {"name": "Newtown"})
    new_id = Branch.objects.get(name="Newtown").id

    settings = client.get("/settings/").content.decode()
    assert f'<label for="goal-{new_id}" data-sensitive>Newtown</label>' in settings
    assert f'name="goal-{new_id}" step="0.1" min="1.0" max="5.0" value=""' in settings

    dashboard = client.get("/dashboard/").content.decode()
    row = dashboard[dashboard.index("Newtown") :]
    assert "No reviews yet" in row[: row.index("</tr>")]

    assert f'<option value="{new_id}">Newtown</option>' in client.get("/reviews/").content.decode()
    compare = client.get("/compare/").content.decode()
    assert compare.count(f'<option value="{new_id}">Newtown</option>') == 2


@pytest.mark.parametrize(
    ("typed", "error"),
    [
        ("", NAME_ERROR),
        ("   ", NAME_ERROR),
        ("x" * 121, NAME_ERROR),
        ("downtown", TAKEN_ERROR),
        ("  DOWN   TOWN ", TAKEN_ERROR),
    ],
)
def test_invalid_post_saves_nothing_and_shows_the_error(
    client: Client, typed: str, error: str
) -> None:
    make("Downtown", "Down Town")
    response = client.post(URL, {"name": typed})
    html = response.content.decode()
    assert response.status_code == 200
    assert Branch.objects.count() == 2
    section = panel(html)
    assert f'<p class="settings-error">{error}</p>' in section
    assert 'aria-describedby="location-name-error" aria-invalid="true"' in section
    assert section.index('id="location-name"') < section.index('id="location-name-error"')
    assert 'id="locations-saved"' not in html


def test_post_without_a_name_field_is_refused(client: Client) -> None:
    response = client.post(URL, {})
    assert response.status_code == 200
    assert NAME_ERROR in panel(response.content.decode())
    assert Branch.objects.count() == 0


def test_invalid_post_keeps_the_typed_name_and_the_other_panels(client: Client) -> None:
    (downtown,) = make("Downtown")
    html = client.post(URL, {"name": " downtown "}).content.decode()
    assert 'name="name" maxlength="120" value=" downtown "' in panel(html)
    assert "reviews/settings.html" in [t.name for t in client.post(URL, {"name": ""}).templates]
    for panel_id in ("settings-account", "settings-goals", "settings-templates"):
        assert f'id="{panel_id}"' in html
    assert 'id="settings-suggestions"' in html
    assert f'<label for="goal-{downtown.id}" data-sensitive>Downtown</label>' in html
    assert "Change password</button>" in html
    for target in re.findall(r'aria-describedby="([^"]+)"', html):
        for element_id in target.split():
            assert f'id="{element_id}"' in html


def test_a_name_with_markup_is_escaped(client: Client) -> None:
    client.post(URL, {"name": "<b>Tom & Co</b>"})
    html = panel(client.get("/settings/").content.decode())
    assert "<b>" not in html
    assert 'aria-label="Rename &lt;b&gt;Tom &amp; Co&lt;/b&gt;"' in html


def test_visitor_is_sent_to_sign_in_and_adds_nothing(db: None) -> None:
    response = Client().post(URL, {"name": "Downtown"})
    assert response.status_code == 302
    assert response["Location"] == f"/login/?next={URL}"
    assert Branch.objects.count() == 0


def test_post_without_csrf_token_is_403(client: Client) -> None:
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(get_user_model().objects.get(username="demo"))
    assert strict.post(URL, {"name": "Downtown"}).status_code == 403
    assert Branch.objects.count() == 0


@pytest.mark.parametrize("location_count", [0, 3, 200])
def test_settings_page_makes_at_most_four_queries_whatever_the_locations(
    client: Client, location_count: int, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    make(*[f"Location {index:03d}" for index in range(location_count)])
    with django_assert_max_num_queries(4):
        html = client.get("/settings/").content.decode()
    assert panel(html).count(">Rename</a>") == location_count


def test_valid_post_makes_at_most_seven_queries(
    client: Client, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    make(*[f"Location {index:03d}" for index in range(200)])
    with django_assert_max_num_queries(7):
        assert client.post(URL, {"name": "Newtown"}).status_code == 302
