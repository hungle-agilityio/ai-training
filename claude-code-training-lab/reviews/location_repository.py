from dataclasses import dataclass

from django.db import transaction

from reviews.models import Branch, Business

DEFAULT_BUSINESS_NAME = "My business"


@dataclass(frozen=True)
class Location:
    location_id: int
    name: str


def add_location(name: str) -> int:
    """Add a location to the business with the lowest id; the first one creates the business."""
    with transaction.atomic():
        business_id = Business.objects.order_by("id").values_list("id", flat=True).first()
        if business_id is None:
            business_id = Business.objects.create(name=DEFAULT_BUSINESS_NAME).id
        return Branch.objects.create(business_id=business_id, name=name).id


def rename_location(location_id: int, name: str) -> None:
    """Only the name changes: reviews, goal and score stay."""
    Branch.objects.filter(id=location_id).update(name=name)


def get_location(location_id: int) -> Location | None:
    """Id and name of one location; None when it does not exist."""
    row = Branch.objects.filter(id=location_id).values_list("id", "name").first()
    if row is None:
        return None
    return Location(location_id=row[0], name=row[1])


def other_location_names(location_id: int) -> list[str]:
    """Names of all locations except the given one, by name then id, in one query."""
    names = Branch.objects.exclude(id=location_id).order_by("name", "id")
    return list(names.values_list("name", flat=True))
