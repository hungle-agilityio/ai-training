from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import Client
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.forms import ReviewFilterForm
from reviews.models import Branch, Business, Review, ReviewFollowUp
from reviews.repositories import create_review
from reviews.services import REVIEWS_PER_PAGE, ReviewFilters, reviews_page

NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
# Text of the review → rating and stored status (None: nothing stored).
CASES: dict[str, tuple[int, str | None]] = {
    "never touched": (1, None),
    "stored open": (2, "open"),
    "called back": (2, "contacted"),
    "all solved": (1, "resolved"),
    "middle one": (3, None),
    "happy one": (5, None),
}
BADGE = '<span class="badge followup-badge followup-{status}">{label}</span>'


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Demo"), name="Hanoi")


def add_review(branch: Branch, rating: int, text: str, status: str | None = None) -> Review:
    review = create_review(branch=branch, rating=rating, text=text, created_at=NOW)
    if status is not None:
        ReviewFollowUp.objects.create(review=review, status=status, updated_at=NOW)
    return review


@pytest.fixture
def cases(branch: Branch) -> Branch:
    for text, (rating, status) in CASES.items():
        add_review(branch, rating, text, status)
    return branch


def page_of(client: Client, **params: str) -> str:
    return client.get("/reviews/", params).content.decode()


def shown_texts(content: str) -> set[str]:
    return {text for text in CASES if text in content}


def export_of(client: Client, **params: str) -> list[str]:
    response = client.get("/reviews/export/", params)
    body = b"".join(response.streaming_content).decode()  # type: ignore[attr-defined]
    return body.lstrip("﻿").splitlines()


def test_followup_filter_comes_after_the_reply_filter_with_four_choices(
    client: Client, cases: Branch
) -> None:
    content = page_of(client)

    assert '<label for="filter-followup">Follow-up</label>' in content
    assert 'id="filter-followup" name="followup"' in content
    select = content.split('id="filter-followup"')[1].split("</select>")[0]
    assert [line.strip() for line in select.splitlines() if "<option" in line] == [
        '<option value="" selected>All</option>',
        '<option value="open">Open</option>',
        '<option value="contacted">Contacted</option>',
        '<option value="resolved">Resolved</option>',
    ]
    assert (
        content.index('id="filter-reply"')
        < content.index('id="filter-followup"')
        < content.index('id="filter-week"')
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("open", {"never touched", "stored open"}),
        ("contacted", {"called back"}),
        ("resolved", {"all solved"}),
    ],
)
def test_followup_filter_keeps_the_bad_reviews_in_that_status(
    client: Client, cases: Branch, status: str, expected: set[str]
) -> None:
    content = page_of(client, followup=status)

    assert shown_texts(content) == expected
    assert f'<option value="{status}" selected>' in content
    assert f"{len(expected)} review" in content


def test_no_followup_filter_keeps_every_review(client: Client, cases: Branch) -> None:
    assert shown_texts(page_of(client)) == set(CASES)


@pytest.mark.parametrize("value", ["closed", "OPEN", "open ", "1", "open'--"])
def test_unknown_followup_value_is_ignored_and_other_filters_apply(
    client: Client, cases: Branch, value: str
) -> None:
    content = page_of(client, followup=value, rating="1")

    assert shown_texts(content) == {"never touched", "all solved"}
    assert "followup=" not in content
    assert '<option value="" selected>All</option>' in content.split('id="filter-followup"')[1]
    assert "/reviews/export/?rating=1" in content


def test_followup_filter_combines_with_the_other_filters(client: Client, cases: Branch) -> None:
    other = Branch.objects.create(business=cases.business, name="Hue")
    add_review(other, 2, "other branch open")

    content = page_of(client, followup="open", rating="2", location=str(cases.id))

    assert shown_texts(content) == {"stored open"}
    assert "other branch open" not in content


def test_good_rating_with_a_followup_status_gives_the_usual_empty_list(
    client: Client, cases: Branch
) -> None:
    content = page_of(client, followup="open", rating="good")

    assert "No reviews found" in content
    assert 'href="/reviews/">Clear</a>' in content


def test_followup_filter_is_kept_in_page_links_and_export_link(
    client: Client, branch: Branch
) -> None:
    for number in range(REVIEWS_PER_PAGE + 1):
        add_review(branch, 2, f"open {number}")

    content = page_of(client, followup="open", reply="no")

    assert 'href="?reply=no&amp;followup=open&amp;page=2"' in content
    assert 'href="/reviews/export/?reply=no&amp;followup=open"' in content
    assert 'href="/reviews/">Clear</a>' in content


def test_followup_filter_alone_shows_clear_and_counts_as_filtered(cases: Branch) -> None:
    page = reviews_page(None, filters=ReviewFilters(followup="resolved"))

    assert (page.followup, page.is_filtered, page.show_clear) == ("resolved", True, True)
    assert page.query_params == [("followup", "resolved")]
    assert page.export_query == "followup=resolved"
    assert page.followup_options == (
        ("open", "Open"),
        ("contacted", "Contacted"),
        ("resolved", "Resolved"),
    )


def test_form_gives_the_followup_status_and_drops_an_unknown_one() -> None:
    assert ReviewFilterForm({"followup": "contacted"}).filters().followup == "contacted"
    assert ReviewFilterForm({"followup": "nope", "rating": "bad"}).filters() == ReviewFilters(
        rating="bad"
    )
    assert ReviewFilterForm({}).filters().followup is None


def test_every_bad_review_row_shows_its_status_badge(client: Client, cases: Branch) -> None:
    page = reviews_page(None)

    assert {row.text: (row.followup, row.followup_label) for row in page.rows} == {
        "never touched": ("open", "Open"),
        "stored open": ("open", "Open"),
        "called back": ("contacted", "Contacted"),
        "all solved": ("resolved", "Resolved"),
        "middle one": ("", ""),
        "happy one": ("", ""),
    }
    content = page_of(client)
    assert '<th scope="col">Follow-up</th>' in content
    assert content.count(BADGE.format(status="open", label="Open")) == 2
    assert content.count(BADGE.format(status="contacted", label="Contacted")) == 1
    assert content.count(BADGE.format(status="resolved", label="Resolved")) == 1
    assert content.count("followup-badge") == 4


def test_three_to_five_star_rows_show_no_badge(client: Client, branch: Branch) -> None:
    for rating in (3, 4, 5):
        add_review(branch, rating, f"{rating} stars")
    # A case stored on a review that is no longer bad must not show a badge either.
    add_review(branch, 4, "was bad once", "resolved")

    content = page_of(client)

    assert "followup-badge" not in content
    assert content.count('<tr class="review-row">') == 4


def test_export_with_followup_filter_has_the_reviews_of_the_list(
    client: Client, cases: Branch
) -> None:
    for status, expected in [
        ("open", ["stored open", "never touched"]),
        ("contacted", ["called back"]),
        ("resolved", ["all solved"]),
    ]:
        lines = export_of(client, followup=status)
        page = reviews_page(None, filters=ReviewFilters(followup=status))

        assert lines[0] == "Location,Rating,Review text,Date"
        assert [line.split(",")[2] for line in lines[1:]] == [row.text for row in page.rows]
        assert sorted(row.text for row in page.rows) == sorted(expected)


def test_export_with_unknown_followup_value_exports_every_review(
    client: Client, cases: Branch
) -> None:
    assert len(export_of(client, followup="closed")) == len(CASES) + 1


def test_export_columns_and_file_name_do_not_change(client: Client, cases: Branch) -> None:
    plain = client.get("/reviews/export/")
    filtered = client.get("/reviews/export/", {"followup": "open"})
    with_location = client.get("/reviews/export/", {"followup": "open", "location": str(cases.id)})

    assert filtered["Content-Disposition"] == plain["Content-Disposition"]
    assert "reviews-hanoi-" in with_location["Content-Disposition"]
    assert filtered["Content-Type"] == plain["Content-Type"]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"followup": "open"},
        {"followup": "contacted"},
        {"followup": "resolved"},
        {"followup": "closed"},
        {
            "followup": "open",
            "rating": "bad",
            "reply": "no",
            "search": "review number",
            "topic": "wait",
            "week": "2026-11-02",
        },
    ],
)
def test_reviews_page_runs_at_most_three_queries_whatever_the_number_of_reviews(
    client: Client,
    branch: Branch,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    params: dict[str, str],
) -> None:
    other = Branch.objects.create(business=branch.business, name="Hue")
    statuses = [None, "open", "contacted", "resolved"]
    for number in range(60):
        add_review(
            branch if number % 2 else other,
            1 + number % 5,
            f"review number {number} waiting",
            statuses[number % 4] if number % 5 < 2 else None,
        )

    with django_assert_max_num_queries(3):
        response = client.get("/reviews/", {**params, "location": str(branch.id)})

    assert response.status_code == 200


def test_export_with_followup_filter_does_not_run_a_query_per_review(
    client: Client, branch: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    for number in range(40):
        add_review(branch, 2, f"open {number}")

    with django_assert_max_num_queries(3):
        assert len(export_of(client, followup="open")) == 41


def test_other_pages_keep_their_query_counts(
    client: Client, cases: Branch, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_max_num_queries(3):
        client.get("/dashboard/")
    with django_assert_max_num_queries(5):
        client.get(f"/locations/{cases.id}/")
    with django_assert_max_num_queries(2):
        client.get("/replies/")


def test_demo_data_open_filter_shows_the_three_airport_cases(client: Client, db: None) -> None:
    call_command("seed_demo_data", stdout=StringIO())

    page = reviews_page(None, filters=ReviewFilters(followup="open"))

    assert page.total == 3
    assert {row.branch_name for row in page.rows} == {"Airport"}
    assert {row.followup for row in page.rows} == {"open"}
    content = page_of(client, followup="open")
    assert content.count(BADGE.format(status="open", label="Open")) == 3
