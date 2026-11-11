import pytest
from django.test import Client

from reviews.models import Branch, Business

ADD_LOCATION_LINK = '<a href="/settings/#settings-locations">Add a location</a>'


@pytest.mark.django_db
def test_empty_dashboard_links_to_the_locations_panel() -> None:
    content = Client().get("/dashboard/").content.decode()

    assert ADD_LOCATION_LINK in content


@pytest.mark.django_db
def test_empty_dashboard_keeps_its_title_and_text() -> None:
    content = Client().get("/dashboard/").content.decode()

    assert "<h2>No locations yet</h2>" in content
    assert "Add your first location and import its reviews to see scores here." in content


@pytest.mark.django_db
def test_dashboard_with_locations_has_no_add_location_link() -> None:
    business = Business.objects.create(name="Demo")
    Branch.objects.create(business=business, name="Riverside")

    content = Client().get("/dashboard/").content.decode()

    assert "Add a location" not in content
    assert "/settings/#settings-locations" not in content
    assert "No locations yet" not in content
