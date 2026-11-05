# Spec: review-replies

## Summary

Staff can write one reply per review and edit it later. A new page `/replies/` ("Reply drafts" in the sidebar, no longer "Soon") lists the reviews that have no reply, worst rating first and oldest first, 20 per page. A new page `/reviews/<id>/reply/` shows one review with a form to write or edit its reply; after saving, the user goes back to `/replies/` and sees "Reply saved.". The review list shows "Replied" or "Not replied" on every row with a link to the reply page, and gets a "Reply" filter. The dashboard gets a "Need a reply" tile. The demo data gives a reply to every review rated 4 or 5. This adds one model, `ReviewReply`, and one migration that only creates its table. The work is one epic issue with six sub-task issues (`tasks.md`). The live site changes only at the release after the whole epic is merged (ADR-017).

## Acceptance criteria

Reply data (T1):

- **AC1.** `reviews/models.py` gets `ReviewReply`: `review` (one-to-one to `Review`, `related_name="reply"`, deleted with the review), `text` (`TextField`), `replied_by` (foreign key to the user model, `null=True`, `blank=True`, set to null when the user is deleted, `related_name="+"`), `created_at` and `updated_at` (`DateTimeField`, set by the code, no `auto_now`). A new migration `reviews/migrations/0004_reviewreply.py` only creates this table; `uv run python manage.py makemigrations --check --dry-run` reports no changes.
- **AC2.** A new module `reviews/reply_repository.py` is the only place that reads or writes `ReviewReply`. `save_reply(*, review_id: int, text: str, user_id: int | None, now: datetime) -> None` creates the reply of a review, or updates its `text`, `replied_by` and `updated_at` and keeps its `created_at`. A review never has two replies.
- **AC3.** A new module `reviews/reply_service.py` has the constant `REPLY_MAX_LENGTH = 1000` and `clean_reply_text(text: str) -> str | None`: the text without spaces and line breaks at both ends, or None when that is empty or longer than 1000 characters (1000 is allowed, 1001 is not).
- **AC4.** `reply_service` has the frozen dataclasses `ReplyInfo(text: str, updated_at: datetime, replied_by: str | None)` and `ReplyTarget(review_id: int, branch_id: int, branch_name: str, rating: int, rating_percent: int, text: str, created_at: datetime, reply: ReplyInfo | None)`, and `reply_target(review_id: int) -> ReplyTarget | None` that reads a review, its location, its reply and the reply's user in one query; None when the review does not exist. `replied_by` is the user name, or None when there is no user.
- **AC5.** `reply_service.save_reply(review_id: int, text: str, user_id: int | None, now: datetime) -> bool` saves the cleaned text (AC3) and returns True; it returns False and saves nothing when the review does not exist or the text is not valid.
- **AC6.** Deleting a review deletes its reply; deleting a user keeps the reply with `replied_by` None.
- **AC7.** Tests in new files `reviews/tests/unit/test_reply_text.py` and `reviews/tests/integration/test_reply_data.py` cover AC1 to AC6, including 1000 and 1001 characters, a text of only spaces, an update keeping `created_at`, and the query count of `reply_target`.

Reply drafts page (T2):

- **AC8.** `reviewradar/urls.py` adds `path("replies/", views.replies, name="replies")`. `GET /replies/` answers 200 with the page title `Reply drafts · ReviewRadar`, the heading "Reply drafts" and the subtitle "Reviews that still need a reply, worst first."; the "Export JSON" button is not shown.
- **AC9.** The sidebar item "Reply drafts" becomes a link to `/replies/` in the same place (after "Reports"), without "Soon" and without `is-disabled` / `aria-disabled`; it is marked active (`is-active`, `aria-current="page"`) on `/replies/`. "Settings" stays as it is.
- **AC10.** A panel `id="reply-queue"` lists only reviews with no reply. Order: ratings 1 and 2 first, then 3, then 4 and 5; inside each group the oldest `created_at` first, then the lowest id. A line above the table says "8 reviews need a reply" ("1 review needs a reply" for one). The table has the headers "Location", "Rating", "Review text" and "Date", shown like the Reviews page: location name linking to `/locations/<id>/`, stars with `aria-label="2 out of 5"`, the text shortened to 120 characters with `data-sensitive="review-text"`, the relative date.
- **AC11.** 20 reviews per page with the same pager as the Reviews page ("Showing 1-20 of 25 reviews", Previous / Next); `?page=` is read with `PageForm`, and a wrong or too high page shows the nearest valid page.
- **AC12.** When no review needs a reply (no reviews at all, or every review has one), the panel shows the heading "All caught up" and the line "Every review has a reply." and no table.
- **AC13.** A visitor who is not signed in gets a 302 to `/login/?next=/replies/`. Without sign-in checks the page makes at most 2 queries, the same for 5 or 500 reviews. At 360px wide the table scrolls inside its panel (`table-wrap`) and the page does not scroll sideways. New styles of this epic go in a new file `reviews/static/reviews/replies.css`, linked from `base.html`.
- **AC14.** Tests in a new file `reviews/tests/integration/test_replies_page.py` cover AC8 to AC13; the sign-in test is marked `login`.

Reply page (T3):

- **AC15.** `reviewradar/urls.py` adds `path("reviews/<int:pk>/reply/", views.review_reply, name="review-reply")`. An id with no review answers the app's 404 page. Methods other than GET and POST answer 405.
- **AC16.** `GET` answers 200 with the page title `Reply to a review · ReviewRadar`, the heading "Reply to a review" and the subtitle "Write the reply your team will post."; no "Export JSON" button. A panel shows the review: location name linking to `/locations/<id>/`, stars with `aria-label`, the full date (`full_review_date`) and the full text with `data-sensitive="review-text"`. "Reply drafts" is active in the sidebar.
- **AC17.** A form `id="reply-form"` (`method="post"`, with `{% csrf_token %}`) has a `textarea` `id="reply-text"`, `name="text"`, `maxlength="1000"`, `required`, `data-sensitive="reply-text"`, labelled "Your reply", with the hint "Up to 1,000 characters.", a "Save reply" button and a link "Back to reply drafts" to `/replies/`. When the review has a reply, the textarea holds it and a line under the form says "Last saved <full date> by <user name>" (the user name with `data-sensitive`), or "Last saved <full date>" when the user is gone.
- **AC18.** A valid `POST` (AC3, read by a new `ReplyForm` in `reviews/forms.py`) saves the reply with the signed-in user (None when there is none) and answers 302 to `/replies/?saved=1`. `/replies/?saved=1` shows the line "Reply saved." (`role="status"`) above the list; any other value of `saved` shows nothing. The review now has a reply, so it is no longer in the list.
- **AC19.** An empty, only-spaces or too long `POST` answers 200 with the same page, the line "Write a reply of 1 to 1,000 characters." (class `alert`), the typed text kept in the textarea, and nothing saved. A `POST` without the CSRF token answers 403.
- **AC20.** Each row of the Reply drafts list gets a last column "Reply" with a button-styled link "Reply" to `/reviews/<id>/reply/`.
- **AC21.** A visitor who is not signed in gets a 302 to the login page with `next`. Without sign-in checks a `GET` makes at most 1 query and a valid `POST` at most 4.
- **AC22.** Tests in a new file `reviews/tests/integration/test_reply_page.py` cover AC15 to AC21; the sign-in test is marked `login`.

Dashboard tile (T4):

- **AC23.** `DashboardOverview` gets `needs_reply_count: int`, the number of reviews (all locations) with no reply. The KPI row gets a fifth tile `id="kpi-needs-reply"` after "Need attention": label "Need a reply", the number, and a link "Open reply drafts" to `/replies/`; the hint says "Reviews with no reply yet", or "Every review has a reply" when the number is 0.
- **AC24.** The dashboard keeps its 3 queries (the existing test stays green): the number is counted inside an existing query, for example the rating counts. With no location the dashboard still shows only "No locations yet".
- **AC25.** The five tiles fit one row on a wide screen and two per row under the existing 1100px breakpoint; at 360px the page does not scroll sideways.
- **AC26.** Tests in a new file `reviews/tests/integration/test_dashboard_needs_reply.py` cover AC23 to AC25.

Review list (T5):

- **AC27.** `ReviewRow` gets `review_id: int` and `has_reply: bool`. The repository functions that read reviews for rows (`reviews_newest_first`, `list_recent_reviews`) also join the reply, so no page and no export makes an extra query: the Reviews page stays at most 3 queries, the CSV export at most 3, the dashboard 3, the location page at most 4 (existing tests stay green).
- **AC28.** The Reviews table gets a last column "Reply": a badge "Replied" (classes `reply-status reply-done`) or "Not replied" (`reply-status reply-open`), and a link "Edit reply" or "Reply" to `/reviews/<id>/reply/`.
- **AC29.** The filters get a select `id="filter-reply"`, `name="reply"`, labelled "Reply", with "All" (`""`), "Replied" (`yes`) and "Not replied" (`no`), read by `ReviewFilterForm`; a wrong value is ignored and the other filters still apply. The chosen value is kept in the pager links and the "Export CSV" link, and "Clear" removes it. The CSV export follows the filter; its columns do not change.
- **AC30.** Tests in a new file `reviews/tests/integration/test_reviews_reply_status.py` cover AC27 to AC29.

Demo replies (T6):

- **AC31.** `seed_demo_data` gives every review rated 4 or 5 one reply, written through `reply_service.save_reply` with the text "Thank you for your kind words. We hope to see you again soon.", `replied_by` None and the seed's `now`. Reviews rated 1 to 3 get none. The extra branches of `--branches` follow the same rule. The default seed makes 6 replies, so 8 of the 14 reviews need a reply; seeding twice still gives 6.
- **AC32.** Every existing test still passes unchanged. Tests in a new file `reviews/tests/integration/test_seed_demo_replies.py` cover AC31.

After the release:

- **AC33.** After all six pull requests are merged, one release (`ops/release.py`, ADR-017) puts the epic on Render. Signed in as `demo`, the owner sees "Need a reply: 8" on the dashboard, opens "Reply drafts", answers the first review, sees "Reply saved." and 7 left, finds the review as "Replied" on the Reviews page with the "Reply" filter, and then closes the epic.

## Edge cases

- Empty: no review needs a reply shows "All caught up" (AC12); the dashboard tile shows 0 and "Every review has a reply"; no location keeps the dashboard's "No locations yet".
- Large data: 500 reviews need the same queries as 5 (AC13, AC21, AC24, AC27).
- Wrong input: an empty, only-spaces or 1001-character reply is refused and kept in the box (AC19); a wrong `page`, `reply` or `saved` value is ignored (AC11, AC18, AC29); an unknown review id gives 404 (AC15).
- Permissions: every page needs sign-in (AC13, AC21); every signed-in user may write or edit any reply; the form needs the CSRF token (AC19).
- Dates: dates show in Vietnam time like the rest of the app; ordering always ends with the id.
- Personal data: review text, reply text and the user name carry `data-sensitive`.
- Data: deleting a review deletes its reply; deleting a user keeps the reply (AC6). The migration only adds a table, so it is safe on the Render database that is seeded on every start.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How a reply is stored | One reply per review (text, user, times) | Draft plus "mark as sent" | Simple; there is no channel to send to yet |
| Q2 Text rules | Required, trimmed, 1 to 1000 characters, edit only | Also a delete button | Keeps the scope small; delete can come later |
| Q3 Order of Reply drafts | Ratings 1-2, then 3, then 4-5; oldest first; 20 per page | Oldest first only; newest first | Bad reviews hurt most; oldest first so none is forgotten |
| Q4 Sidebar name | Keep "Reply drafts", now active | Rename to "Replies" | An existing test pins "Reply drafts" and the loop may not edit it; the reply is a draft staff post elsewhere |
| Q5 Review list | Badge, link and a "Reply" filter; reply text only on its page | Also the reply text under each review | Keeps rows short and less personal data on the list |
| Q6 Dashboard | A "Need a reply" tile, no extra query | No change | Shows the work to do at a glance; the query count test stays green |
| Q7 After saving | Back to `/replies/` with "Reply saved." | Stay on the reply page | Fast to answer one review after the other; no `next` parameter, so no open redirect |
| Q8 Demo data | Replies for the 4 and 5 star reviews | No demo replies | Every state is visible on Render |

## Design

Design card linked in `design/review-replies/README.md`.

## Open questions
