# Spec: location-page

## Summary

A new page `/locations/<id>/` shows one location: its score, its rating breakdown, a weekly trend for the last 8 weeks and its 5 newest reviews. The dashboard gets a "Details" link on each location row and the review list turns the location name into a link to that page. Read only: no model change, no migration. The work is one epic issue with four sub-task issues (`tasks.md`); T1 and T2 run side by side, then T3 and T4 run side by side. The live site changes only at the release after the whole epic is merged (ADR-017).

## Acceptance criteria

Location page (T1):

- **AC1.** `reviewradar/urls.py` adds `path("locations/<int:pk>/", views.location, name="location")`. For an existing location, `GET /locations/<id>/` answers 200 with the page title `<location name> · ReviewRadar`, the heading `<location name>`, the subtitle "Score, weekly trend and latest reviews for this location." and no "Export JSON" button (the `actions` block is empty).
- **AC2.** A "Score" panel shows the location's average rating to one decimal, rounded half up through `average_from_totals` (Riverside in the demo data: 3.4), the stars, the status badge with the same rule and texts as the dashboard (Excellent, Watch, Needs attention) and the line "<n> reviews" ("1 review" for one). A location with no reviews shows "No reviews yet" and "0 reviews", and no stars and no badge.
- **AC3.** A "Rating breakdown" panel lists 5, 4, 3, 2 and 1 stars, each with its count for this location only and a bar whose width is `round(count / total * 100)` percent, as on the dashboard. With no reviews every count is 0 and every bar is empty. The bars are not links.
- **AC4.** A "Latest reviews" panel shows the 5 newest reviews of this location (newest first, ties by higher id first) with the Rating, Review text, Sentiment and Date cells of the Reviews page (no Location column); the review text cell carries `data-sensitive`. Under it, a link "See all reviews" opens `/reviews/?location=<id>`. With no reviews the panel shows "No reviews yet" and "Reviews will appear here as soon as they are imported." and no "See all reviews" link.
- **AC5.** `/locations/<id>/` for an id that does not exist answers 404 with the existing 404 page; `/locations/abc/` answers 404 too.
- **AC6.** A visitor who is not signed in gets a 302 to `/login/?next=/locations/<id>/`.
- **AC7.** Without sign-in checks, the page makes at most 3 database queries, the same for a location with 5 or with 200 reviews. Queries live in `reviews/repositories.py`; rules live in `reviews/services.py`, which returns frozen dataclasses; the view stays thin.
- **AC8.** At 360px wide the panels stack in one column and the page does not scroll sideways. Tests for AC1 to AC7 are in a new file `reviews/tests/integration/test_location_page.py`; the test for AC6 is marked `login`.

Weekly trend numbers (T2):

- **AC9.** A new module `reviews/trend_service.py` has `weekly_trend(branch_id: int, now: datetime) -> list[WeekPoint]` and the constant `TREND_WEEKS = 8`. `WeekPoint` is a frozen dataclass with `monday: date`, `label: str`, `review_count: int`, `average_rating: float | None` and `bar_percent: int`.
- **AC10.** It returns exactly 8 points, oldest first. The last point is the week (Monday 00:00 to the next Monday 00:00, Vietnam time) that contains `now` in Vietnam time, whatever time zone is active. `label` is the Monday as `"Oct 26"` (`f"{monday:%b} {monday.day}"`).
- **AC11.** A review belongs to the week that contains its `created_at` in Vietnam time: Sunday 23:59 Vietnam time counts in that week, Monday 00:00 in the next one.
- **AC12.** `average_rating` comes from `average_from_totals` (one decimal, half up; a week with ratings 5, 2, 4, 2 gives 3.3); a week with no reviews has `review_count` 0, `average_rating` None (never 0) and `bar_percent` 0. Otherwise `bar_percent` is `round(average_rating / 5 * 100)`.
- **AC13.** Reviews of other locations, and reviews before the first Monday or from the next Monday on, are not counted. All 8 weeks are read with one query, in a new module `reviews/trend_repository.py`, the same for 5 or 200 reviews.
- **AC14.** Tests in new files `reviews/tests/unit/test_weekly_trend.py` and `reviews/tests/integration/test_weekly_trend_query.py` cover AC9 to AC13, including the Sunday/Monday edge, a time zone other than Vietnam, and the query count.

Trend chart (T3):

- **AC15.** The location page has a "Weekly trend" panel, with the line "Average rating per week, last 8 weeks (Monday to Sunday)", between the Score/Rating breakdown panels and "Latest reviews", as on the design card.
- **AC16.** The chart shows 8 columns, oldest on the left. A week with reviews has a bar of height `bar_percent`% with its average above it ("3.3"); a week with no reviews has no bar and "–". Under each column: the week label and the review count.
- **AC17.** Under the chart, a table with the headers "Week of", "Average" and "Reviews" lists the 8 weeks; a week with no reviews shows "No reviews" in the Average column. The bars themselves are `aria-hidden`, so a screen reader reads the table.
- **AC18.** The chart is HTML and CSS only (styles in `app.css`, light and dark): no JavaScript, no image, no file from another site. At 360px wide all 8 columns fit and the page does not scroll sideways.
- **AC19.** The page makes at most 4 queries without sign-in checks (AC7 plus the trend query), the same for 5 or 200 reviews.
- **AC20.** Tests in a new file `reviews/tests/integration/test_location_trend.py` cover AC15 to AC19 with fixed review dates (the test sets `now`, not the real clock).

Links to the page (T4):

- **AC21.** The dashboard's "Location scores" table gets a last column headed "Details". Each row, including a location with no reviews, has a link with the text "Details" and `aria-label="Details for <location name>"` to `/locations/<id>/`. The location name link stays `/reviews/?location=<id>`.
- **AC22.** The dashboard's "Latest reviews" panel does not change: location names there stay plain text.
- **AC23.** On the Reviews page, the location name in each row is a link to `/locations/<id>/` with the same name text. `ReviewRow` gets a `branch_id: int` field filled from `review.branch_id`, with no extra query.
- **AC24.** The query counts of the dashboard (3) and of the Reviews page do not change. No existing test changes.
- **AC25.** Tests in a new file `reviews/tests/integration/test_location_links.py` cover AC21 to AC24.

After the release:

- **AC26.** After all four pull requests are merged, one release (`ops/release.py`, ADR-017) puts the epic on Render. The owner opens a location from the dashboard on the live site, signed in as `demo`, and sees the page of the design card; then the owner closes the epic.

## Edge cases

- Empty: a location with no reviews shows "No reviews yet", 0 counts, 8 empty weeks and no "See all reviews" link (AC2, AC3, AC4, AC12).
- Large data: 200 reviews on one location need the same number of queries as 5 (AC7, AC13, AC19); only 5 reviews are listed.
- Dates: the week is Monday to Sunday in Vietnam time, even when the server runs in UTC (AC10, AC11). On Render the demo data is 0 to 4 days old, so only the last one or two weeks have bars; that is expected.
- Wrong input: an unknown or non-numeric id answers the 404 page (AC5).
- Permissions: every page needs sign-in (AC6); every signed-in user sees every location.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Trend window | Last 8 weeks, current week included | 12 weeks, 4 weeks | Enough to see a direction; the demo data still shows in it |
| Q2 Value per week | Average score and review count | Review count only | The MVP asks for a score trend; the count shows how much each average can be trusted |
| Q3 Reviews on the page | 5 newest and "See all reviews" | None | Gives the reason behind the score without repeating the review list |
| Q4 Dashboard link | Keep the name link, add a "Details" link | Name links to the new page | An existing test fixes the name link and the loop may not edit tests, so the whole epic stays `agent:ready` |
| Q5 Review list | Location name links to the page | No change | One click from a review to its location |
| Q6 Chart | Server-rendered HTML/CSS bars and a number table, no JavaScript | A JS chart library from a CDN | Nothing new to load, easy to test, readable by a screen reader |
| Q7 Release | One release after all four pull requests are merged | A release per pull request | ADR-017: one release per sprint or epic |
| Trend code placement (from the analysis, not asked) | New modules `reviews/trend_service.py` and `reviews/trend_repository.py` | Add to `services.py` and `repositories.py` | T1 and T2 run side by side and may not share a file; the layers stay the same |

## Design

Design card: see `design/location-page/README.md`.

## Open questions
