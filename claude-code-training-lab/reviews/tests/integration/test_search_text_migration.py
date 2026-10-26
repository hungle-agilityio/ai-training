import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from reviews.search_text import normalize_for_search

BEFORE = [("reviews", "0001_initial")]
AFTER = [("reviews", "0003_backfill_review_search_text")]


def _migrate(targets: list[tuple[str, str]]) -> MigrationExecutor:
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection)


@pytest.mark.django_db(transaction=True)
def test_migration_fills_the_search_text_of_existing_reviews_and_goes_back() -> None:
    executor = _migrate(BEFORE)
    try:
        old_apps = executor.loader.project_state(BEFORE).apps
        business = old_apps.get_model("reviews", "Business").objects.create(name="Demo")
        branch = old_apps.get_model("reviews", "Branch").objects.create(
            business=business, name="Airport"
        )
        review_model = old_apps.get_model("reviews", "Review")
        for index, text in enumerate(("ĐAU CHÂN", "Parking Full", "")):
            review_model.objects.create(
                branch=branch, rating=3, text=text, created_at=f"2026-10-14T0{index}:00:00Z"
            )

        executor = _migrate(AFTER)
        new_model = executor.loader.project_state(AFTER).apps.get_model("reviews", "Review")
        stored = {review.text: review.search_text for review in new_model.objects.all()}
        assert stored == {
            "ĐAU CHÂN": normalize_for_search("ĐAU CHÂN"),
            "Parking Full": "parking full",
            "": "",
        }

        _migrate(BEFORE)
    finally:
        _migrate(executor.loader.graph.leaf_nodes())
