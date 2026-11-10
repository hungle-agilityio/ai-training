import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from reviews import template_repository
from reviews.models import ReplyTemplate


@pytest.mark.django_db
def test_list_all_orders_by_name_ignoring_case_then_id() -> None:
    b = template_repository.create_template(name="b", text="t", kind="any")
    upper_a = template_repository.create_template(name="A", text="t", kind="any")
    lower_a = template_repository.create_template(name="a", text="t", kind="any")

    with CaptureQueriesContext(connection) as queries:
        result = list(template_repository.list_templates())

    assert [t.id for t in result] == [upper_a.id, lower_a.id, b.id]
    assert len(queries) == 1


@pytest.mark.django_db
def test_list_for_kinds_filters_and_uses_one_query() -> None:
    good = template_repository.create_template(name="G", text="t", kind="good")
    template_repository.create_template(name="B", text="t", kind="bad")
    anyone = template_repository.create_template(name="A", text="t", kind="any")

    with CaptureQueriesContext(connection) as queries:
        result = list(template_repository.list_templates_for_kinds(("good", "any")))

    assert [t.id for t in result] == [anyone.id, good.id]
    assert len(queries) == 1


@pytest.mark.django_db
def test_get_template_returns_none_when_missing() -> None:
    created = template_repository.create_template(name="X", text="t", kind="bad")

    assert template_repository.get_template(created.id) == created
    assert template_repository.get_template(created.id + 1) is None


@pytest.mark.django_db
def test_update_template_changes_name_text_and_kind() -> None:
    created = template_repository.create_template(name="X", text="t", kind="bad")

    template_repository.update_template(created.id, name="Y", text="new", kind="good")

    saved = ReplyTemplate.objects.get(id=created.id)
    assert (saved.name, saved.text, saved.kind) == ("Y", "new", "good")


@pytest.mark.django_db
def test_delete_template_removes_only_that_one() -> None:
    first = template_repository.create_template(name="X", text="t", kind="bad")
    second = template_repository.create_template(name="Z", text="t", kind="bad")

    template_repository.delete_template(first.id)

    assert list(ReplyTemplate.objects.values_list("id", flat=True)) == [second.id]


@pytest.mark.django_db
def test_name_exists_ignores_case_and_excluded_id() -> None:
    created = template_repository.create_template(name="Thank You", text="t", kind="any")

    assert template_repository.name_exists("thank you") is True
    assert template_repository.name_exists("thank you", exclude_id=created.id) is False
    assert template_repository.name_exists("other") is False
