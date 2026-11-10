from collections.abc import Iterable

from django.db.models import QuerySet
from django.db.models.functions import Lower

from reviews.models import ReplyTemplate


def _ordered() -> QuerySet[ReplyTemplate]:
    return ReplyTemplate.objects.order_by(Lower("name"), "id")


def list_templates() -> QuerySet[ReplyTemplate]:
    """All templates by name ignoring case, then id."""
    return _ordered()


def list_templates_for_kinds(kinds: Iterable[str]) -> QuerySet[ReplyTemplate]:
    """The templates of the given kinds, in the same order as list_templates."""
    return _ordered().filter(kind__in=list(kinds))


def get_template(template_id: int) -> ReplyTemplate | None:
    return ReplyTemplate.objects.filter(id=template_id).first()


def create_template(*, name: str, text: str, kind: str) -> ReplyTemplate:
    return ReplyTemplate.objects.create(name=name, text=text, kind=kind)


def update_template(template_id: int, *, name: str, text: str, kind: str) -> None:
    ReplyTemplate.objects.filter(id=template_id).update(name=name, text=text, kind=kind)


def delete_template(template_id: int) -> None:
    ReplyTemplate.objects.filter(id=template_id).delete()


def name_exists(name: str, exclude_id: int | None = None) -> bool:
    """Whether another template has this name, ignoring case."""
    found = ReplyTemplate.objects.filter(name__iexact=name)
    if exclude_id is not None:
        found = found.exclude(id=exclude_id)
    return found.exists()
