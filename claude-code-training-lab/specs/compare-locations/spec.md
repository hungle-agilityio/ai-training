# Spec: compare-locations

## Summary

A new page `/compare/?a=<location id>&b=<location id>&period=<"" | 30 | 90>` puts two locations side by side for a period. It reuses the existing rules: score (`average_from_totals`), good and bad bands (`RATING_RANGES`), bad review and 24-hour window (`BAD_RATINGS`, `REPLY_WINDOW`), whole percent half up (`topic_service.percent`), topics (`TOPICS`, `topic_repository.topic_totals`). The sidebar gets a "Compare" link and each location page a "Compare with another location" button. The comparison downloads as CSV. No migration. One epic, five tasks, all `agent:ready`.

## Definitions

- **Period:** `""` all time (default), `30` last 30 days, `90` last 90 days, counted back from now on `created_at` (the choices of `topic_forms.PERIOD_CHOICES`).
- **Good / bad share:** reviews of rating 4 to 5 / 1 to 2 in the period, as a whole percent of the period's reviews, half up; `None` (shown "—") when the location has no review in the period.
- **Replied in 24h:** of the bad reviews in the period that are counted (they have a reply, or are more than 24 hours old), the whole percent replied within 24 hours, half up (`reply_share_percent`); `None` ("—") when none is counted.
- **Difference:** score of A minus score of B, one decimal, from the two rounded scores with `Decimal` (never float subtraction); `None` when either has no score.

## Acceptance criteria

Compare rule and data (T1):

- **AC1.** `reviews/compare_repository.py` (NEW) reads, in one query for both locations, per location: id, name, review count, rating total, the count of each star 1 to 5, bad counted, bad replied in 24 hours, all limited to reviews created at or after the period start (no limit for all time). A location with no review in the period still comes back with zeros.
- **AC2.** `reviews/compare_service.py` (NEW) `compare_locations(a_id, b_id, period_days, now) -> Comparison | None` returns frozen dataclasses: `Comparison(period_days, period_label, a: LocationSide, b: LocationSide, difference: float | None)`, `LocationSide(branch_id, name, review_count: int, average_rating: float | None, good_percent: int | None, bad_percent: int | None, replied_in_time_percent: int | None, star_rows: tuple[StarRow, ...])`, `StarRow(stars: int, count: int, percent: int)` for 5 down to 1. It returns `None` when either id is not a location or both ids are the same. Period labels: "All time", "Last 30 days", "Last 90 days".
- **AC3.** Demo data (fresh `seed_demo_data`, all time): Downtown 5 reviews, score 4.0, good 60, bad 0, replied in 24h `None`, stars 5:2 (40), 4:1 (20), 3:2 (40), 2:0 (0), 1:0 (0); Riverside 5 reviews, score 3.4, good 60, bad 40, replied in 24h 100, stars 5:1 (20), 4:2 (40), 3:0 (0), 2:2 (40), 1:0 (0); difference Downtown − Riverside `0.6`. Airport 4 reviews, score 2.0, good 0, bad 75, replied in 24h 0. Last 30 days: Downtown 2 reviews 4.5, Riverside 2 reviews 4.5, difference `0.0`. Tests assert these numbers and their types (`float`, `int`, `None`).

Compare page (T2):

- **AC4.** `/compare/` (url name `compare`, signed in) has the title "Compare locations · ReviewRadar", heading "Compare locations", subtitle "Two locations side by side for a period." and a form `#compare-form` (GET) with two location selects "Location A" and "Location B" (every location, by name, plus an empty "Choose a location" option) and a period select (All time, Last 30 days, Last 90 days), and a "Compare" button; no "Export JSON" button. The inputs are read through a Django form (`reviews/compare_forms.py`, NEW); an unknown or invalid id counts as not chosen, an invalid period as all time, never an error page.
- **AC5.** With two different locations chosen, the page shows a table `#compare-table` with a header row (blank, A's name, B's name; location names are not personal data, so no `data-sensitive`) and rows: "Score" (one decimal, or "No score yet"), "Reviews", "Good reviews" (percent or "—"), "Bad reviews" (percent or "—"), "Replied in 24h" (percent or "—"), then one row per star 5 to 1 with count and percent ("5 ★  2 (40%)"). Above the table a line: "<A> scores <difference> higher than <B>" when the difference is positive, "<A> scores <|difference|> lower than <B>" when negative, "Same score" when 0.0, nothing when `None`.
- **AC6.** Nothing chosen, or only one location: no table; the text "Pick two locations to compare." under the form. The same location twice: no table; the message "Choose two different locations." in the `--bad` colour under the form.
- **AC7.** `/compare/` makes at most 2 database queries with two locations chosen (location list + compare data), whatever the number of reviews; tests assert it.
- **AC8.** At 360 px wide the form fields stack and the table fits or scrolls inside its own panel; the page itself never scrolls sideways. Styles go in `reviews/static/reviews/app.css`, using its existing tokens in light and dark.

Entry points (T3):

- **AC9.** The sidebar gets a "Compare" item between "Topics" and "Reply drafts", linking to `/compare/`, active (`is-active`, `aria-current="page"`) on `/compare/` only. Every existing sidebar test passes unchanged.
- **AC10.** Each location page gets a button "Compare with another location" in the page header actions (`{% block actions %}`, class `button`), linking to `/compare/?a=<its id>`; the compare page then has that location chosen as A. The location page makes no extra query.

Topics side by side (T4):

- **AC11.** Below the table, a panel `#compare-topics` "What customers talk about" lists the topics of `TOPICS` in their order, with for each side the number of reviews and, when above 0, the bad ones ("2 · 1 bad"). A topic with 0 reviews on both sides is left out. When no topic has reviews on either side: "No topics found for these locations in this period."
- **AC12.** Demo data, Downtown (A) vs Riverside (B), all time: Wait time 1 / 0; Staff 2 / 1 · 1 bad; Doctor & treatment 1 / 2; Price & billing 1 / 0; Booking & phone 0 / 1 · 1 bad; Parking 1 / 1; Cleanliness 1 / 0. Last 30 days: Staff 1 / 0; Doctor & treatment 0 / 1; Parking 0 / 1; Cleanliness 1 / 0.
- **AC13.** With the panel, `/compare/` makes at most 4 queries (AC7 plus one topic query per location).

CSV export (T5):

- **AC14.** With a valid comparison the page shows a "Download CSV" button linking to `/compare/export/?a=..&b=..&period=..` (url name `compare-export`). The file has the UTF-8 marker, header `Measure,<A name>,<B name>`, then rows Reviews, Score, Good reviews %, Bad reviews %, Replied in 24h %, 5 stars, 4 stars, 3 stars, 2 stars, 1 star (counts), with empty cells for `None`; every cell goes through `csv_safe`. File name `compare-<slug A>-<slug B>-<all-time|30-days|90-days>.csv` with `location_slug`.
- **AC15.** An export without a valid comparison (missing, unknown or equal locations) redirects (302) to `/compare/` with the same query string. The export makes at most 1 query for the numbers plus the location lookup.

All tasks:

- **AC16.** New tests only, in the new files named in each task; every existing test passes unchanged. `ruff`, `mypy --strict` and `pytest` pass.

## Edge cases

- A location with no review in the period: "No score yet", "0" reviews, "—" for the shares, every star row "0 (0%)", no topic counts.
- Location names with Vietnamese letters: shown as typed; the CSV name uses `location_slug`.
- A location deleted between page load and Compare: treated as not chosen (AC4).
- Many reviews: the query count does not grow (AC7, AC13).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Feature for the test epic | Compare two locations | Rating breakdown everywhere; Claude sentiment | Useful to a multi-branch owner, no migration, five tasks with two levels of dependencies |
| Q2. Period | All time, last 30, last 90 days (as Topics) | A month picker (as Reports) | Same choices users already know from Topics |
| Q3. How many locations | Two | Any number | Keeps the page and the table simple |

## Design

Design card: see `design/compare-locations/README.md`.

## Open questions
