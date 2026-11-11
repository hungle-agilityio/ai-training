from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from pytest_django.fixtures import DjangoAssertNumQueries

from reviews.models import Branch, Business, Review, ReviewFollowUp, ReviewReply

NOW = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)
STATUS_ERROR = "Choose a status from the list."
NOTE_ERROR = "Write a note of at most 500 characters."


@pytest.fixture
def branch(db: None) -> Branch:
    return Branch.objects.create(business=Business.objects.create(name="Biz"), name="Clinic A")


@pytest.fixture
def review(branch: Branch) -> Review:
    return review_of(branch, 2)


@pytest.fixture
def user(db: None) -> User:
    return get_user_model().objects.create_user(username="anna", password="x")


def review_of(branch: Branch, rating: int) -> Review:
    return Review.objects.create(
        branch=branch, rating=rating, text="Waited an hour.", created_at=NOW - timedelta(days=2)
    )


def reply_url(review: Review) -> str:
    return f"/reviews/{review.id}/reply/"


def followup_url(review: Review) -> str:
    return f"/reviews/{review.id}/follow-up/"


def box(page: str) -> str:
    """The Follow-up section of a reply page."""
    start = page.index('<section class="panel followup" id="followup">')
    return page[start : page.index("</section>", start)]


def store_case(review: Review, user: User | None = None) -> ReviewFollowUp:
    return ReviewFollowUp.objects.create(
        review=review, status="contacted", note="Called back.", updated_by=user, updated_at=NOW
    )


@pytest.mark.parametrize("rating", [1, 2])
def test_bad_review_shows_the_box_below_the_reply_form(branch: Branch, rating: int) -> None:
    review = review_of(branch, rating)

    page = Client().get(reply_url(review)).content.decode()
    section = box(page)

    assert page.index('id="reply-form"') < page.index('id="followup"')
    assert "<h2>Follow-up</h2>" in section
    assert f'method="post" action="{followup_url(review)}"' in section
    assert "csrfmiddlewaretoken" in section
    assert '<label for="followup-status">Status</label>' in section
    assert '<select id="followup-status" name="status">' in section
    assert '<label for="followup-note">Internal note</label>' in section
    assert 'name="note"' in section
    assert 'maxlength="500"' in section
    assert "data-sensitive" in section[section.index("<textarea") : section.index("</textarea>")]
    assert 'aria-describedby="note-help"' in section
    assert '<p class="field-hint" id="note-help">Only your team sees this note.</p>' in section
    assert "Save follow-up</button>" in section
    assert "Follow-up saved." not in page
    assert "aria-invalid" not in section


def test_statuses_are_listed_in_order_with_open_selected_when_nothing_is_stored(
    review: Review,
) -> None:
    section = box(Client().get(reply_url(review)).content.decode())

    options = section[section.index("<select") : section.index("</select>")]
    assert options.index(">Open<") < options.index(">Contacted<") < options.index(">Resolved<")
    assert '<option value="open" selected>Open</option>' in options
    assert options.count("selected") == 1
    assert options.count("<option") == 3
    assert "></textarea>" in section
    assert "Not changed yet." in section
    assert "Last changed" not in section


def test_stored_case_shows_status_note_and_last_change_by_user(review: Review, user: User) -> None:
    store_case(review, user)

    section = box(Client().get(reply_url(review)).content.decode())

    assert '<option value="contacted" selected>Contacted</option>' in section
    assert section.count("selected") == 1
    assert ">Called back.</textarea>" in section
    assert "Last changed Nov 5, 2026, 17:00 by <span data-sensitive>anna</span>" in section
    assert "Not changed yet." not in section


def test_stored_case_without_user_has_no_by(review: Review) -> None:
    store_case(review)

    section = box(Client().get(reply_url(review)).content.decode())

    assert "Last changed Nov 5, 2026, 17:00</p>" in section
    assert " by " not in section


def test_note_is_escaped(review: Review) -> None:
    ReviewFollowUp.objects.create(
        review=review, status="open", note="<b>refund</b> & call", updated_at=NOW
    )

    section = box(Client().get(reply_url(review)).content.decode())

    assert "&lt;b&gt;refund&lt;/b&gt; &amp; call" in section
    assert "<b>refund</b>" not in section


@pytest.mark.parametrize("rating", [3, 4, 5])
def test_review_of_three_to_five_stars_shows_no_box(branch: Branch, rating: int) -> None:
    response = Client().get(reply_url(review_of(branch, rating)))
    page = response.content.decode()

    assert response.status_code == 200
    assert 'id="followup"' not in page
    assert "Follow-up" not in page
    assert "Save reply" in page


def test_get_of_the_post_address_redirects_to_the_reply_page(review: Review) -> None:
    response = Client().get(followup_url(review))

    assert response.status_code == 302
    assert response["Location"] == reply_url(review)
    assert not ReviewFollowUp.objects.exists()


@pytest.mark.parametrize("method", ["put", "delete", "patch"])
def test_other_methods_answer_405(review: Review, method: str) -> None:
    assert getattr(Client(), method)(followup_url(review)).status_code == 405


def test_valid_post_saves_status_stripped_note_and_time_then_redirects(review: Review) -> None:
    before = timezone.now()

    response = Client().post(
        followup_url(review), {"status": "contacted", "note": "  Called back.\n"}
    )

    assert response.status_code == 302
    assert response["Location"] == f"{reply_url(review)}?followup=saved#followup"
    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by) == ("contacted", "Called back.", None)
    assert before <= case.updated_at <= timezone.now()


def test_valid_post_stores_the_signed_in_user(review: Review, user: User) -> None:
    client = Client()
    client.force_login(user)

    client.post(followup_url(review), {"status": "resolved", "note": ""})

    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by) == ("resolved", "", user)


def test_second_post_updates_the_one_case(review: Review, user: User) -> None:
    store_case(review, user)

    Client().post(followup_url(review), {"status": "resolved", "note": "Refunded."})

    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by) == ("resolved", "Refunded.", None)
    assert case.updated_at > NOW


def test_note_of_exactly_500_characters_after_stripping_is_saved(review: Review) -> None:
    response = Client().post(followup_url(review), {"status": "open", "note": f"  {'a' * 500}  "})

    assert response.status_code == 302
    assert ReviewFollowUp.objects.get(review=review).note == "a" * 500


def test_line_break_of_the_browser_counts_as_one_character(review: Review) -> None:
    typed = "\r\n".join(["a" * 99] * 5) + "b"

    response = Client().post(followup_url(review), {"status": "open", "note": typed})

    assert response.status_code == 302
    note = ReviewFollowUp.objects.get(review=review).note
    assert len(note) == 500
    assert "\r" not in note


def test_saved_notice_shows_after_the_redirect(review: Review) -> None:
    store_case(review)

    section = box(Client().get(f"{reply_url(review)}?followup=saved").content.decode())

    assert '<p class="notice" id="followup-saved" role="status">Follow-up saved.</p>' in section


@pytest.mark.parametrize("query", ["", "?followup=1", "?followup=", "?saved=1"])
def test_no_saved_notice_without_the_saved_value(review: Review, query: str) -> None:
    page = Client().get(f"{reply_url(review)}{query}").content.decode()

    assert "followup-saved" not in page
    assert "Follow-up saved." not in page


def test_saved_value_shows_nothing_on_a_review_without_a_case(branch: Branch) -> None:
    page = Client().get(f"{reply_url(review_of(branch, 4))}?followup=saved").content.decode()

    assert "Follow-up" not in page


def test_follow_up_post_does_not_change_the_reply(review: Review, user: User) -> None:
    ReviewReply.objects.create(
        review=review, text="Sorry!", replied_by=user, created_at=NOW, updated_at=NOW
    )

    Client().post(followup_url(review), {"status": "contacted", "note": "Called."})

    reply = ReviewReply.objects.get(review=review)
    assert (reply.text, reply.replied_by, reply.created_at, reply.updated_at) == (
        "Sorry!",
        user,
        NOW,
        NOW,
    )


def test_saving_a_reply_does_not_change_the_follow_up(review: Review, user: User) -> None:
    store_case(review, user)

    response = Client().post(reply_url(review), {"text": "Sorry about the wait."})

    assert response.status_code == 302
    assert response["Location"] == "/replies/?saved=1"
    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_by, case.updated_at) == (
        "contacted",
        "Called back.",
        user,
        NOW,
    )


def test_saving_a_reply_creates_no_case(review: Review) -> None:
    Client().post(reply_url(review), {"text": "Sorry about the wait."})

    assert not ReviewFollowUp.objects.exists()


def test_too_long_note_saves_nothing_and_keeps_what_was_typed(review: Review) -> None:
    store_case(review)
    typed = "b" * 501

    response = Client().post(followup_url(review), {"status": "resolved", "note": typed})
    page = response.content.decode()
    section = box(page)

    assert response.status_code == 200
    case = ReviewFollowUp.objects.get(review=review)
    assert (case.status, case.note, case.updated_at) == ("contacted", "Called back.", NOW)
    assert '<option value="resolved" selected>Resolved</option>' in section
    assert section.count("selected") == 1
    assert f">{typed}</textarea>" in section
    assert f'<p class="field-error" id="note-error">{NOTE_ERROR}</p>' in section
    textarea = section[section.index("<textarea") : section.index("</textarea>")]
    assert 'aria-invalid="true"' in textarea
    assert 'aria-describedby="note-error note-help"' in textarea
    assert section.index("</textarea>") < section.index('id="note-error"')
    assert STATUS_ERROR not in section
    assert "status-error" not in section
    assert "Follow-up saved." not in page
    assert "Save reply" in page
    assert "Waited an hour." in page


def test_unknown_status_saves_nothing_and_shows_the_error_under_the_status(
    review: Review,
) -> None:
    response = Client().post(followup_url(review), {"status": "closed", "note": "Kept note"})
    section = box(response.content.decode())

    assert response.status_code == 200
    assert not ReviewFollowUp.objects.exists()
    assert f'<p class="field-error" id="status-error">{STATUS_ERROR}</p>' in section
    select = section[section.index("<select") : section.index("</select>")]
    assert 'aria-invalid="true"' in select
    assert 'aria-describedby="status-error"' in select
    assert "selected" not in select
    assert section.index("</select>") < section.index('id="status-error"')
    assert ">Kept note</textarea>" in section
    assert NOTE_ERROR not in section
    assert 'id="note-error"' not in section


def test_missing_fields_and_long_note_show_both_errors(review: Review) -> None:
    response = Client().post(followup_url(review), {"note": "c" * 600})
    section = box(response.content.decode())

    assert response.status_code == 200
    assert not ReviewFollowUp.objects.exists()
    assert STATUS_ERROR in section
    assert NOTE_ERROR in section


def test_invalid_post_shows_the_stored_reply_text(review: Review) -> None:
    ReviewReply.objects.create(review=review, text="Sorry!", created_at=NOW, updated_at=NOW)

    page = Client().post(followup_url(review), {"status": "closed"}).content.decode()

    assert "Sorry!</textarea>" in page
    assert "Write a reply of 1 to 1,000 characters." not in page


def test_unknown_review_answers_404(db: None) -> None:
    response = Client().post("/reviews/999/follow-up/", {"status": "open", "note": ""})

    assert response.status_code == 404


@pytest.mark.parametrize("rating", [3, 4, 5])
def test_post_for_three_to_five_stars_answers_404_and_saves_nothing(
    branch: Branch, rating: int
) -> None:
    review = review_of(branch, rating)

    response = Client().post(followup_url(review), {"status": "contacted", "note": "x"})

    assert response.status_code == 404
    assert not ReviewFollowUp.objects.exists()


@pytest.mark.login
def test_visitor_not_signed_in_is_sent_to_sign_in(review: Review) -> None:
    response = Client().post(followup_url(review), {"status": "contacted", "note": "x"})

    assert response.status_code == 302
    assert response["Location"] == f"/login/?next={followup_url(review)}"
    assert not ReviewFollowUp.objects.exists()


@pytest.mark.login
def test_signed_in_user_reads_and_saves_with_the_sign_in_check_on(
    review: Review, user: User
) -> None:
    client = Client()
    client.force_login(user)

    saved = client.post(followup_url(review), {"status": "contacted", "note": "Called."})
    section = box(client.get(saved["Location"]).content.decode())

    assert "Follow-up saved." in section
    assert "by <span data-sensitive>anna</span>" in section


def test_reply_page_get_still_makes_at_most_two_queries_with_a_stored_case(
    review: Review, user: User, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    store_case(review, user)
    ReviewReply.objects.create(
        review=review, text="Sorry!", replied_by=user, created_at=NOW, updated_at=NOW
    )

    with django_assert_max_num_queries(2):
        Client().get(f"{reply_url(review)}?followup=saved")


@pytest.mark.login
@pytest.mark.parametrize("stored", [False, True])
def test_follow_up_post_makes_at_most_five_queries(
    review: Review,
    user: User,
    stored: bool,
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    if stored:
        store_case(review, user)
    client = Client()
    client.force_login(user)

    with django_assert_max_num_queries(5):
        response = client.post(followup_url(review), {"status": "resolved", "note": "Done."})

    assert response.status_code == 302
    assert ReviewFollowUp.objects.get(review=review).status == "resolved"


@pytest.mark.login
def test_invalid_follow_up_post_makes_at_most_five_queries(
    review: Review, user: User, django_assert_max_num_queries: DjangoAssertNumQueries
) -> None:
    client = Client()
    client.force_login(user)

    with django_assert_max_num_queries(5):
        response = client.post(followup_url(review), {"status": "closed", "note": ""})

    assert response.status_code == 200


def test_box_styles_live_in_replies_css() -> None:
    text = (Path(__file__).parents[2] / "static/reviews/replies.css").read_text()

    assert ".followup-form" in text
    assert ".followup .field-error" in text
