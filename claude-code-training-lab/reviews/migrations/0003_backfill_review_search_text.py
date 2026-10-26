from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

from reviews.search_text import normalize_for_search

CHUNK_SIZE = 500


def backfill(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Fill the search copy of every review; a change of the search rule needs a new backfill migration."""
    review_model = apps.get_model("reviews", "Review")
    pending = []
    for review in review_model.objects.only("id", "text").iterator(chunk_size=CHUNK_SIZE):
        review.search_text = normalize_for_search(review.text)
        pending.append(review)
        if len(pending) >= CHUNK_SIZE:
            review_model.objects.bulk_update(pending, ["search_text"], batch_size=CHUNK_SIZE)
            pending = []
    if pending:
        review_model.objects.bulk_update(pending, ["search_text"], batch_size=CHUNK_SIZE)


class Migration(migrations.Migration):
    dependencies = [
        ("reviews", "0002_review_search_text"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
