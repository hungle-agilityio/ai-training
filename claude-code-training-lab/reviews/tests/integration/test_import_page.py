from pathlib import Path
from typing import cast

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client

from reviews.models import Branch, Business, Review

pytestmark = [pytest.mark.django_db, pytest.mark.login]

HEADER = "Location,Rating,Review text,Date\n"
SAMPLE = Path(__file__).resolve().parents[2] / "static" / "reviews" / "import-sample.csv"


@pytest.fixture
def client(db: None) -> Client:
    user: User = get_user_model().objects.create_user(username="demo", password="pw-long-enough-1")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def branches(db: None) -> None:
    business = Business.objects.create(name="Demo")
    for name in ("Downtown", "Riverside", "Airport"):
        Branch.objects.create(business=business, name=name)


def upload(client: Client, content: bytes | str) -> HttpResponse:
    data = content.encode() if isinstance(content, str) else content
    file = SimpleUploadedFile("reviews.csv", data, content_type="text/csv")
    return cast(HttpResponse, client.post("/reviews/import/", {"file": file}))


def test_reviews_page_has_import_button_before_export(client: Client) -> None:
    page = client.get("/reviews/").content.decode()
    assert 'id="import-csv"' in page
    assert 'href="/reviews/import/"' in page
    assert page.index("Import CSV") < page.index("Export CSV")


def test_get_page_shows_form_and_links(client: Client) -> None:
    response = client.get("/reviews/import/")
    page = response.content.decode()
    assert response.status_code == 200
    assert "Import reviews" in page
    assert (
        "Add reviews from a CSV file with the columns Location, Rating, Review text and Date."
        in page
    )
    assert "CSV file" in page
    assert 'accept=".csv' in page
    assert ">Import</button>" in page
    assert "Download a sample file" in page
    assert "import-sample.csv" in page
    assert "Back to reviews" in page
    assert "csrfmiddlewaretoken" in page
    assert 'aria-current="page"' in page.split("Reviews")[0] + page  # sidebar marks Reviews


def test_sidebar_marks_reviews_current(client: Client) -> None:
    page = client.get("/reviews/import/").content.decode()
    marker = 'href="/reviews/" aria-current="page"'
    assert marker in page


def test_sample_file_is_exact() -> None:
    assert SAMPLE.read_text() == (
        HEADER
        + "Downtown,5,Friendly staff and a short wait.,2026-11-01 09:30\n"
        + "Riverside,2,Could not get through on the phone.,2026-11-02 14:05\n"
        + "Airport,4,Clean rooms and kind nurses.,2026-11-03\n"
    )


def test_sample_imports_then_counts_duplicates(client: Client, branches: None) -> None:
    first = upload(client, SAMPLE.read_bytes()).content.decode()
    assert 'id="import-result"' in first
    assert "3 reviews imported" in first
    assert "0 duplicates skipped" in first
    assert "0 rows with errors" in first
    assert 'href="/reviews/"' in first and "See the reviews" in first
    assert 'type="file"' in first
    assert Review.objects.count() == 3
    second = upload(client, SAMPLE.read_bytes()).content.decode()
    assert "0 reviews imported" in second
    assert "3 duplicates skipped" in second
    assert Review.objects.count() == 3


def test_singular_labels(client: Client, branches: None) -> None:
    body = HEADER + "Downtown,5,ok,2026-11-01\nDowntown,9,bad,2026-11-01\n"
    page = upload(client, body).content.decode()
    assert "1 review imported" in page
    assert "1 row with errors" in page
    again = upload(client, HEADER + "Downtown,5,ok,2026-11-01\n").content.decode()
    assert "1 duplicate skipped" in again


def test_bad_row_listed_without_review_text(client: Client, branches: None) -> None:
    body = (
        HEADER
        + "Downtown,5,fine,2026-11-01\n"
        + "Airprot,4,secret-words,2026-11-01\n"
        + "Downtown,9,hidden-text,2026-11-01\n"
    )
    page = upload(client, body).content.decode()
    assert 'id="import-errors"' in page
    assert "<th>Row</th>" in page and "<th>Problem</th>" in page
    assert "Airprot" in page
    assert "secret-words" not in page and "hidden-text" not in page
    assert "table-wrap" in page
    assert Review.objects.count() == 1


def test_more_than_50_errors_are_cut(client: Client, branches: None) -> None:
    body = HEADER + "".join(f"Downtown,9,x{i},2026-11-01\n" for i in range(60))
    page = upload(client, body).content.decode()
    assert page.count("<tr><td>") == 50
    assert "and 10 more rows with errors" in page


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("Location,Rating\nA,5\n", "The file needs the columns"),
        (b"\xff\xfe\x00bad", "Save the file as CSV UTF-8 and try again."),
        (HEADER, "The file has no reviews."),
        (b"x" * 1_048_577, "The file is too large"),
    ],
)
def test_refused_file_shows_message_and_saves_nothing(
    client: Client, branches: None, content: bytes | str, message: str
) -> None:
    page = upload(client, content).content.decode()
    assert 'id="import-error"' in page
    assert message in page
    assert 'aria-invalid="true"' in page
    assert 'id="import-result"' not in page
    assert Review.objects.count() == 0


def test_too_many_rows_is_refused(client: Client, branches: None) -> None:
    body = HEADER + "Downtown,5,t,2026-11-01\n" * 2_001
    page = upload(client, body).content.decode()
    assert "at most 2,000 reviews and 1 MB" in page
    assert Review.objects.count() == 0


def test_post_without_file(client: Client) -> None:
    page = client.post("/reviews/import/", {}).content.decode()
    assert 'id="import-error"' in page
    assert "Choose a CSV file to import." in page
    assert 'aria-invalid="true"' in page


def test_signed_out_goes_to_login() -> None:
    response = Client().get("/reviews/import/")
    assert response.status_code == 302
    assert response["Location"].startswith("/login/")


def test_put_is_not_allowed(client: Client) -> None:
    assert client.put("/reviews/import/").status_code == 405
