# Spec: overdue-replies

## Summary

A bad review with no reply after 24 hours is overdue. The Reply drafts page `/replies/` shows an "Overdue" label on those rows and gets two tabs, "All" and "Overdue only" (`/replies/?overdue=1`). The "Need a reply" card on `/dashboard/` gets one more line with the number of overdue reviews and a link to that list. No migration, no new query, no change to the demo data.

## Definitions

- **Bad review:** rating 1 or 2 (`BAD_RATINGS` in `reviews/repositories.py`).
- **Overdue review:** a bad review with no reply whose `created_at` is more than 24 hours before now (`REPLY_WINDOW`). A review exactly 24:00:00 old is not overdue yet. This is the same review that "Replied in 24h" counts as a miss.
- Hours are clock hours; time zones do not matter, because only the difference of two times is used.

## Acceptance criteria

Overdue rule and data (T1):

- **AC1.** One rule decides "overdue", in `reviews/reply_service.py` (for one review: rating, has reply, `created_at`, now) and in `reviews/reply_repository.py` (the same rule as a query filter). Both use `BAD_RATINGS` and `REPLY_WINDOW` from `reviews/repositories.py`; no other copy of 24 hours or of the ratings is written.
- **AC2.** `reply_repository.reviews_without_reply` takes an optional `overdue_only: bool = False` and an optional `now`; with `overdue_only=True` it returns only overdue reviews, in the same order as today (1 to 2 stars, oldest first, then lowest id). Without the arguments it returns the same as today.
- **AC3.** `reply_service.replies_page` takes optional `overdue_only: bool = False` and `now` (defaults to the current time). Each `ReplyRow` gets `is_overdue: bool`, computed from the row's own data without a query. `RepliesPage` gets `overdue_only: bool`, and its page links and Previous / Next links keep `overdue=1` when it is on. Called as today, it returns the same rows and links as today, with `is_overdue` added.

Reply drafts page (T2):

- **AC4.** `/replies/` shows two tabs above the table, inside `#reply-queue`: "All" (`href="/replies/"`) and "Overdue only" (`href="/replies/?overdue=1"`). The tab of the current view has `aria-current="page"` and the active style. The tabs carry no number.
- **AC5.** `overdue` is read through a Django form: `1` turns the filter on; anything else (`0`, `abc`, empty, missing) shows the "All" view, without an error.
- **AC6.** Each overdue row shows a label "Overdue" next to the stars, with `title="No reply for more than 24 hours"`, styled as a small badge with the `--bad` text on `--bad-soft` tokens from `app.css`, in light and dark. Rows that are not overdue show no label. The label shows in both tabs.
- **AC7.** In "Overdue only", the count line reads "<N> overdue review needs a reply" / "<N> overdue reviews need a reply", and the pager reads "Showing a-b of N reviews" as today; page 2 keeps `overdue=1`.
- **AC8.** "Overdue only" with no overdue review shows the heading "No overdue reviews", the text "Every bad review older than 24 hours has a reply." and a link "Show all reviews" to `/replies/`; no table. The "All" view with no review keeps "All caught up" as today.
- **AC9.** `/replies/` and `/replies/?overdue=1` each make at most 2 database queries for any number of reviews; every existing test in `reviews/tests/integration/test_replies_page.py` passes unchanged.
- **AC10.** At 360 px the tabs wrap or fit, and the page does not scroll sideways.

Dashboard (T3):

- **AC11.** The "Need a reply" card (`#kpi-needs-reply`) gets one more hint line, before "Open reply drafts": "<N> overdue (bad, over 24 h)" as a link to `/replies/?overdue=1` when N > 0, in the `--bad` colour; "None overdue" in `--muted`, without a link, when N = 0.
- **AC12.** N is the sum over locations of the counted bad reviews minus the bad reviews with a reply, from the totals `branch_rating_totals` already reads (`DashboardOverview.overdue_count: int`). `/dashboard/` still makes exactly the same number of queries as today, and every existing dashboard test passes unchanged. `/api/dashboard/` returns the same JSON as today.

Demo data and types (T2, T3):

- **AC13.** On a fresh `seed_demo_data` (just after a restart): the card shows "Need a reply" 5 and "1 overdue (bad, over 24 h)"; "Overdue only" lists one review, Airport 1★ "Billing mistake and nobody called back.", with the label; in "All", that row has the label and Airport 2★ "Waited 50 minutes, nobody apologized." does not (it was created at seed time).
- **AC14.** `overdue_count` is an `int` and `is_overdue` a `bool`; tests assert the types.

## Edge cases

- Empty: no review at all shows "All caught up" in "All" and AC8 in "Overdue only". On the dashboard, no locations shows the existing "No locations yet" panel.
- A bad review younger than 24 hours, or exactly 24 hours old, is not overdue. A bad review with a reply is never overdue, however late the reply was.
- Large data: thousands of overdue reviews still take 2 queries on `/replies/` (paginated, 20 per page) and no extra query on `/dashboard/`.
- Permissions: same as today, every signed-in user; visitors who are not signed in are sent to sign-in.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Feature for the flow test epic | Overdue replies | Needs-attention page (already exists as Reply drafts and "Need a reply"), compare two locations, sentiment by Claude | Keeps the owner's pick without repeating what exists; no migration, no external service |
| What is overdue | 1-2 stars, no reply, older than 24 h | 1-3 stars; 48 h | Same rule as "Replied in 24h", so the numbers agree |
| Reply drafts | Label and "All / Overdue only" tabs without a number | Tabs with a number; label only | A number would need a third query and change an existing test |
| Dashboard | One line in "Need a reply" | A new KPI card; nothing | Smallest change, no new query; lets T2 and T3 run side by side |
| Empty "Overdue only" | "No overdue reviews" | Reuse "All caught up" | "All caught up" would be wrong while reviews still wait |

## Design

`design/overdue-replies/README.md`

## Open questions
