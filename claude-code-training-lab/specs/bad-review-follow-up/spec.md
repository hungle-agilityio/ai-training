# Spec: bad-review-follow-up

## Summary

A new table `ReviewFollowUp` (one row per bad review at most: status, note, who changed it, when) holds the follow-up of bad reviews. A pure rule in `reviews/followup.py` defines the statuses and checks a change. The reply page of a bad review gets a "Follow-up" box to change the status and the internal note. The Reviews page gets a "Follow-up" filter and a status badge on every bad review. The dashboard gets an "Open cases" number with a link to those reviews. `seed_demo_data` gives two demo cases a status. One migration adds the table; saved replies, the Reply drafts page, the location page, the reports, the compare page and the API do not change.

## Acceptance criteria

**The rule (T1)**

- **AC1.** `reviews/followup.py` defines the statuses `open`, `contacted` and `resolved`, in that order, with the labels "Open", "Contacted" and "Resolved". `has_case(rating)` is true for the bad range of `RATING_RANGES` (1 and 2 stars) and false for 3, 4 and 5. `status_of(stored)` returns `open` when nothing is stored, else the stored status.
- **AC2.** `followup_errors(status, note)` returns a list of error messages, empty when the change is valid: a status that is not one of AC1 gives "Choose a status from the list."; a note longer than 500 characters after stripping gives "Write a note of at most 500 characters." An empty note is valid.
- **AC3.** The rule has no database access and no Django model import.

**Storing cases (T2)**

- **AC4.** Model `ReviewFollowUp` with `review` (one-to-one to `Review`, deleted with it, reverse name `followup`), `status` (CharField 10, choices of AC1), `note` (TextField, may be empty), `updated_by` (user, may be empty, set to empty when the user is deleted) and `updated_at`; added by migration `0007_reviewfollowup`. No change to `Review`, `Branch`, `ReviewReply` or `ReplyTemplate`.
- **AC5.** `reviews/followup_repository.py`, the only place that writes cases: save the status, note, user and time of one review (create the row, or update the one row); and a filter condition on reviews for a status: `open` keeps bad reviews with no stored case or a stored `open`; `contacted` and `resolved` keep bad reviews whose stored status is that one. 3 to 5 star reviews never match.
- **AC6.** `seed_demo_data` deletes all cases with the reviews (as today) and stores two:
  - Riverside, "Phone line always busy, could not book.": Contacted, note "Called the customer back and booked a visit for the next morning."
  - Riverside, "Nhân viên lễ tân chưa nhiệt tình": Resolved, note "Talked with the front desk team about greeting every customer."
  Both with no user. The three bad Airport reviews stay Open. Everything else the seed does is unchanged.

**Reply page (T3)**

- **AC7.** The reply page `/reviews/<id>/reply/` of a bad review shows, below the reply form, `<section class="panel followup" id="followup">` titled "Follow-up" with a form: a select "Status" (name `status`, the statuses of AC1 in order, the current one selected), a textarea "Internal note" (name `note`, maxlength 500, `data-sensitive`) with the help "Only your team sees this note.", and a button "Save follow-up". Below the form: "Last changed <date> by <user>" (date in the format the reply uses; " by <user>" left out when no user is stored, the user name carries `data-sensitive`), or "Not changed yet." when no case is stored.
- **AC8.** The reply page of a 3, 4 or 5 star review shows no Follow-up box.
- **AC9.** The form posts to `/reviews/<id>/follow-up/` (POST only; a GET redirects to the reply page). A valid post saves the status, the stripped note, the signed-in user and the time, and redirects to `/reviews/<id>/reply/?followup=saved#followup`, where the notice "Follow-up saved." (`id="followup-saved"`, `role="status"`) shows. The reply is not changed.
- **AC10.** An invalid post (AC2) saves nothing and shows the reply page again with the typed status and note kept and each error under its field, linked by `aria-describedby`. An unknown review, or a 3 to 5 star review, is 404.
- **AC11.** The reply page GET runs at most 2 queries (as on `main`); a follow-up post runs at most 5. Saving a reply does not change the follow-up.

**Reviews page (T4)**

- **AC12.** The Reviews page filter form gets a select "Follow-up" (name `followup`) after the "Reply" filter, with "All", "Open", "Contacted" and "Resolved". A status keeps the reviews of the condition of AC5; an unknown value is ignored and the other filters still apply. The filter is kept in the page links and in the "Export CSV" link.
- **AC13.** Every bad review row of the Reviews page shows a badge with its status label (`<span class="badge followup-badge followup-<status>">`); 3 to 5 star rows show no badge.
- **AC14.** "Export CSV" with the Follow-up filter exports the same reviews as the list; the CSV columns and the file name do not change.
- **AC15.** `/reviews/` runs at most 3 queries with any filter (as on `main`); the location page, the dashboard and the Reply drafts page keep their query counts.

**Dashboard (T5)**

- **AC16.** The dashboard shows, after "Replied in 24h", `<article class="kpi" id="kpi-open-cases">` with the label "Open cases" and the number of bad reviews whose status is Open (AC1; no stored case is Open). When the number is above 0 the hint is "Bad reviews not handled yet" with a link "See open cases" to `/reviews/?followup=open`; at 0 the hint is "No open cases".
- **AC17.** The dashboard still runs exactly 3 queries (the open count comes from a query the page already runs); `/api/dashboard/` does not change.

**All tasks**

- **AC18.** `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its new tests in the new test files it names; existing tests change only where its issue lists them under "Existing tests that change".

## Edge cases

- Empty: no bad reviews → "Open cases" 0 with "No open cases"; the Follow-up filter gives the usual empty list text.
- A bad review that later is deleted: its case goes with it.
- A note with `<` or `&` is escaped like any other text; the note never shows outside the reply page.
- Large data: 1,000 bad reviews → the badge comes with the reviews page query; no query per row.
- Permissions: every signed-in user; visitors are sent to sign in for the new URL.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Which reviews have a case | Only bad reviews (1–2 ★) | Every review | Follow-up is for unhappy customers |
| Q2 Statuses | Open / Contacted / Resolved | Open / Resolved | Shows a customer was called but the problem is not solved yet |
| Q3 Existing bad reviews | No stored case = Open, no data migration | Data migration | One small migration, nothing to back-fill |
| Q4 Storage | New table `ReviewFollowUp` | Fields on `Review` | Keeps `Review` and its queries unchanged |
| Q5 Where to change it | Follow-up box on the reply page | Inline on the Reviews list | One place with the review text and the reply |
| Q6 Note | Optional, at most 500 characters, internal, `data-sensitive` | No note | The team needs to know what was done |
| Q7 Saving a reply changes the status | No | Yes, to Contacted | A public reply is not a contact; no hidden rule |
| Q8 Reviews page | Filter + badge, at most 3 queries | Badge only | Find the open cases quickly |
| Q9 Dashboard | "Open cases" in an existing query, still 3 queries | 4 queries | Six tests pin the dashboard at 3 |
| Q10 History | Current status + last change only | Full history | Smaller first version |
| Q11 Demo data | Two Riverside cases (Contacted, Resolved), Airport stays Open | None | The demo shows all three statuses. Downtown, proposed in grill-me, has no bad review, so the demo cases are on Riverside |

## Design

Design card linked in `design/bad-review-follow-up/README.md`.

## Open questions
