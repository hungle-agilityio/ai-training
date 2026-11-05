# Spec: monthly-report

## Summary

A new page `/reports/?month=YYYY-MM` lists every location with its review count, average score, good and bad reviews for one month in Vietnam time, the change of the average against the month before, and an "Export CSV" button for the same table. "Reports" is added to the sidebar. The demo data spreads its 14 reviews over about 90 days. Read only: no model change, no migration. The work is one epic issue with five sub-task issues (`tasks.md`): T1 → T2 → T3 → T5 is a chain (each waits for the one before it only) and T4 runs on its own from the start. The live site changes only at the release after the whole epic is merged (ADR-017).

## Acceptance criteria

Month numbers (T1):

- **AC1.** A new module `reviews/report_service.py` has the constant `REPORT_MONTHS = 12`, the frozen dataclasses `MonthOption(value: str, label: str)`, `ReportRow(branch_id: int, name: str, review_count: int, average_rating: float | None, good_count: int, bad_count: int)` and `MonthlyReport(month: date, label: str, options: list[MonthOption], rows: list[ReportRow])`, and `monthly_report(month: date | None, now: datetime) -> MonthlyReport`.
- **AC2.** `options` lists the month that contains `now` in Vietnam time and the 11 months before it, newest first; `value` is `"2026-11"`, `label` is `"November 2026"`. `month` is the first day of the chosen month. When `month` is None or not one of the 12 options, the report is for the current month.
- **AC3.** A review belongs to the month that contains its `created_at` in Vietnam time, whatever time zone is active: Oct 31 23:59 Vietnam time counts in October, Nov 1 00:00 in November.
- **AC4.** `rows` has one row per location, including a location with no reviews that month, ordered by name A to Z, then by id. `average_rating` comes from `average_from_totals` (one decimal, half up; ratings 5, 2, 4, 2 give 3.3); with no reviews it is None (never 0) and every count is 0. `good_count` counts ratings 4 and 5, `bad_count` ratings 1 and 2 (`RATING_RANGES`); 3 is in neither.
- **AC5.** All locations of one month are read with one query in a new module `reviews/report_repository.py`, the same for 3 or 30 locations and 5 or 500 reviews.
- **AC6.** Tests in new files `reviews/tests/unit/test_monthly_report.py` and `reviews/tests/integration/test_monthly_report_query.py` cover AC1 to AC5, including the month edge, a time zone other than Vietnam, a month outside the 12, and the query count.

Report page (T2):

- **AC7.** `reviewradar/urls.py` adds `path("reports/", views.reports, name="reports")`. `GET /reports/` answers 200 with the page title `Monthly report · ReviewRadar`, the heading "Monthly report" and the subtitle "Reviews and average score per location for one month (Vietnam time)."; the "Export JSON" button is not shown.
- **AC8.** A form (GET) has a select labelled "Month" with the 12 options of AC2 (current month selected by default, the chosen month selected otherwise) and a "Show" button. A new `ReportMonthForm` in `reviews/forms.py` reads `month` as `YYYY-MM`; a wrong value (`2026-13`, `abc`, a month older than 12 months) is ignored and the current month is shown, with no error message.
- **AC9.** A "Locations" panel shows a table with the headers "Location", "Reviews", "Average", "Good (4–5)" and "Bad (1–2)", one row per location as in AC4. The location name links to `/locations/<id>/`. An average shows to one decimal ("3.4"); no reviews shows "—".
- **AC10.** When no location has a review that month, the table still lists every location and a line under it says "No reviews in <Month YYYY>." (for example "No reviews in July 2026."). When there is no location at all, the panel shows "No locations yet" and no table.
- **AC11.** The sidebar gets a "Reports" item between "Reviews" and "Reply drafts", marked active (`is-active`, `aria-current="page"`) on `/reports/`.
- **AC12.** A visitor who is not signed in gets a 302 to `/login/?next=/reports/`.
- **AC13.** Without sign-in checks, the page makes at most 1 database query. At 360px wide the table scrolls inside its panel (`table-wrap`) and the page does not scroll sideways.
- **AC14.** Tests in a new file `reviews/tests/integration/test_reports_page.py` cover AC7 to AC13 with a fixed `now`; the test for AC12 is marked `login`.

Change against the previous month (T3):

- **AC15.** `ReportRow` gets `change: float | None`: this month's average minus the previous month's average, both as shown (one decimal), rounded to one decimal (3.4 − 3.1 = 0.3, never 0.30000000000000004). It is None when either month has no reviews.
- **AC16.** The table gets a last column headed "vs <previous month name>" (for November 2026: "vs October"). It shows "▲ 0.3" (class `change-up`), "▼ 0.5" (class `change-down`), "0.0" (class `change-same`) or "—". Each value has an `aria-label` such as "Up 0.3 from October", "Down 0.5 from October", "Same as October" or "No comparison". Colours come from `app.css`, in light and dark.
- **AC17.** The previous month of January 2026 is December 2025. The page makes at most 2 queries (AC13 plus the previous month), the same for 3 or 30 locations.
- **AC18.** Tests in a new file `reviews/tests/integration/test_reports_change.py` cover AC15 to AC17.

Demo data over three months (T4):

- **AC19.** `seed_demo_data` keeps the same businesses, locations, ratings and texts (14 reviews by default), but the review at position `i` of a location (0 = first in the list) is dated `now − i × 20 days` instead of `now − i days`. So each location's newest review is still today and the oldest default review is 80 days old. The extra branches of `--branches` follow the same rule.
- **AC20.** Every existing test still passes unchanged. Tests in a new file `reviews/tests/integration/test_seed_demo_history.py` check AC19 (offsets 0, 20, 40, 60, 80 days; with a fixed `now`, reviews fall in at least 3 different months).

CSV export (T5):

- **AC21.** `reviewradar/urls.py` adds `path("reports/export/", views.reports_export, name="reports-export")`. The report page shows an "Export CSV" button (in the `actions` block) that opens `/reports/export/?month=<value of the shown month>`.
- **AC22.** The file has the same rows, in the same order, as the page for that month: header `Location,Reviews,Average,Good,Bad,Change vs previous month`; average as `3.4` or empty; change as `+0.3`, `-0.5`, `0.0` or empty. It starts with the BOM and uses `\r\n` line ends like the reviews export, and location names go through `csv_safe`.
- **AC23.** The download name is `reviewradar-report-YYYY-MM.csv` for the month in the file. A wrong `month` value gives the current month's file, as on the page.
- **AC24.** A visitor who is not signed in gets a 302 to the login page. Without sign-in checks the export makes at most 2 queries.
- **AC25.** Tests in a new file `reviews/tests/integration/test_reports_export.py` cover AC21 to AC24.

After the release:

- **AC26.** After all five pull requests are merged, one release (`ops/release.py`, ADR-017) puts the epic on Render. Signed in as `demo`, the owner opens "Reports" in the sidebar, sees the current month with ▲ / ▼ values, picks an earlier month, downloads the CSV, and then closes the epic.

## Edge cases

- Empty: a month with no reviews lists every location with "—" and 0, plus "No reviews in <Month YYYY>." (AC10); no locations shows "No locations yet".
- Large data: 30 locations and 500 reviews need the same queries as 3 and 5 (AC5, AC13, AC17, AC24).
- Dates: months are in Vietnam time even when the server runs in UTC (AC3); January compares with December of the year before (AC17).
- Wrong input: a bad or too old `month` shows the current month (AC8, AC23).
- Permissions: every page needs sign-in (AC12, AC24); every signed-in user sees every location.
- Personal data: the report shows only location names and numbers, no customer text, so no `data-sensitive` and no warning under "Export CSV".

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q0 Feature for this epic | Monthly report | Location ranking, "Needs attention" panel | Splits into a 4-step chain and an independent task, no migration |
| Q1 Default month and picker | Current month, select of the last 12 months | Previous full month; free YYYY-MM input | Like the trend's current week; a list avoids typing errors |
| Q2 Columns | Reviews, average, good, bad | Add neutral; only reviews and average | Good/bad already exist in `RATING_RANGES`; no new rule |
| Q3 Location with no reviews | Row stays, "—" and 0 | Hide the row | "No reviews means no score", and a quiet location is visible |
| Q4 Change vs previous month | Difference of the averages, one decimal, ▲/▼ | Also the count difference; percent | One number, easy to read and check; a percent on a 1–5 scale misleads |
| Q5 Row order | Name A–Z, then id | Average high to low | Rows keep their place from month to month |
| Q6 Demo data | Same 14 reviews, dates spread over 80 days | Add reviews | An existing test fixes 14 reviews and the loop may not edit tests |
| Q7 Extra scope | Add T5 CSV export | No export | Owner's choice |
| Q8 Release | One release after all PRs merge | A release per PR | ADR-017 |
| Q9 CSV content | Same rows and columns as the page, change included | Without the change column | One source of numbers for page and file |
| Split (from the analysis, not asked) | T1 → T2 → T3 → T5 chain, each `Depends on` only its direct parent; T4 alone | One task per layer in parallel | Tests stacked builds (#165) and stacked merges (#180); two open parents would hold a child |

## Design

Design card: see `design/monthly-report/README.md`.

## Open questions
