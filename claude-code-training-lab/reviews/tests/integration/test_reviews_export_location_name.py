import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from reviews.models import Branch, Business


def _disposition(query: str = "") -> str:
    response = Client().get(f"/reviews/export/{query}")
    assert response.status_code == 200
    b"".join(response.streaming_content)  # type: ignore[attr-defined]
    return response["Content-Disposition"]


def _branch(name: str) -> Branch:
    business, _ = Business.objects.get_or_create(name="Demo")
    return Branch.objects.create(business=business, name=name)


@pytest.mark.django_db
def test_location_filter_puts_the_location_in_the_file_name() -> None:
    branch = _branch("Riverside")
    header = _disposition(f"?location={branch.pk}")
    assert header.startswith('attachment; filename="reviews-riverside-')
    assert header.endswith('.csv"')


@pytest.mark.django_db
def test_no_location_keeps_the_date_only_name() -> None:
    _branch("Riverside")
    assert "reviews-riverside" not in _disposition()
    assert _disposition().count("-") == 3  # reviews-YYYY-MM-DD


@pytest.mark.django_db
def test_unknown_location_keeps_the_date_only_name() -> None:
    _branch("Riverside")
    assert "riverside" not in _disposition("?location=9999")


@pytest.mark.django_db
def test_other_filters_do_not_change_the_name() -> None:
    branch = _branch("Riverside")
    plain = _disposition(f"?location={branch.pk}")
    assert _disposition(f"?location={branch.pk}&rating=good&search=x") == plain


@pytest.mark.django_db
def test_symbols_only_name_uses_the_id() -> None:
    branch = _branch("!!!")
    assert f"reviews-location-{branch.pk}-" in _disposition(f"?location={branch.pk}")


@pytest.mark.django_db
def test_location_name_costs_at_most_one_extra_query() -> None:
    branch = _branch("Riverside")
    with CaptureQueriesContext(connection) as plain:
        _disposition()
    with CaptureQueriesContext(connection) as named:
        _disposition(f"?location={branch.pk}")
    assert len(named) <= len(plain) + 1
