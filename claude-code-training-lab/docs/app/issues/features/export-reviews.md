# [FEAT] Export reviews to a spreadsheet file

- **GitHub:** #18
- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-22
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `needs-info`

## Summary

As a manager, I want to download the reviews I see on the Reviews page as a spreadsheet file, so that I can share them with my team and use them in the weekly meeting without copying them by hand. It changes the existing **Reviews** page (`/reviews/`) by adding one button and a short note; it does not add a page.

## Scope

- An "Export CSV" button in the top right of the Reviews page, where the Dashboard has its "Export JSON" button, with a short note about personal details next to it.
- A downloaded file with the reviews that match the filters chosen on the page.

## Not in scope

- Other file types (Excel, PDF).
- Exporting the Dashboard scores (the Dashboard already has its own "Export JSON" button).
- Sending the file by email or on a schedule.
- Choosing which columns go into the file.
- Hiding personal details inside the review text.
- Asking people to log in before they export. The app has no login today; that is a separate matter.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a manager clicks "Export CSV" on the Reviews page without any filter, the screen must offer a download of a file that holds every review, newest first.
- When a manager clicks "Export CSV" while a location, a rating or a week is chosen, the screen must offer a download of only the reviews that match all chosen filters, in the same order as the table.
- When a manager is on page 2 or later of the table and clicks "Export CSV", the screen must offer a file with all matching reviews, not only the 20 shown on that page.
- When a manager clicks "Export CSV", the screen must name the file `reviews-<date of the download>.csv` (Vietnam time), for example `reviews-2026-10-22.csv`. (proposal)
- When a manager clicks "Export CSV", the screen must offer a file with one header row and one row per review, with the columns Location, Rating, Review text and Date, in this order, and Vietnamese letters that Excel and Google Sheets show correctly.
- When a manager looks at the "Export CSV" button, the screen must show next to it the note "The file can contain customers' personal details."
- When the text of a review starts with `=`, `+`, `-` or `@`, the screen must offer a file in which that text is shown as plain text and is never calculated as a formula by a spreadsheet program.
- When there is nothing to show because no review matches the filters, the screen must still offer a file that holds only the header row.

## Scenarios

**Scenario 1: export one location**
- Given Riverside has 3 reviews: rated 4 on 2026-10-14 at 09:30, rated 5 on 2026-10-13 at 18:05 and rated 2 on 2026-10-12 at 07:45 (Vietnam time), and the other locations have more reviews
- When the manager chooses Riverside on the Reviews page, clicks Apply, then clicks "Export CSV"
- Then a file `reviews-2026-10-22.csv` is downloaded with the header row and exactly 3 review rows, newest first

**Scenario 2: nothing matches**
- Given no review of Riverside was written in the week of 2026-10-05
- When the manager chooses Riverside and that week, clicks Apply, then clicks "Export CSV"
- Then a file is downloaded with the header row only

**Scenario 3: a review that looks like a formula**
- Given Airport has a review rated 1 with the text `=HYPERLINK("http://example.com","Click")`
- When the manager clicks "Export CSV" and opens the file in Excel
- Then the cell shows the text `=HYPERLINK("http://example.com","Click")` as plain text, and no link or calculation happens

**Scenario 4: Vietnamese letters**
- Given Riverside has a review with the text `Nhân viên rất nhiệt tình, đau chân đỡ hẳn`
- When the manager clicks "Export CSV" and opens the file in Excel
- Then the cell shows `Nhân viên rất nhiệt tình, đau chân đỡ hẳn` with every letter correct, and the comma does not split the text into two columns

## Spec

- Columns, in order: `Location`, `Rating`, `Review text`, `Date`. There is no Sentiment column.
- Rating is the number of stars, 1 to 5.
- Review text is the complete text, not the shortened text shown in the table.
- Date is the day and time in Vietnam time, written `2026-10-14 09:30`.
- Rows are ordered newest first, the same as the table. Reviews written at the same minute keep a fixed order, so the file is the same every time.
- A filter with a wrong value is ignored, as on the page, and the other filters still apply.
- Text that contains a comma, a quotation mark or a new line must not break the columns of the file.
- A review text that starts with `=`, `+`, `-` or `@` gets a single quote (`'`) in front of it in the file, so that Excel and Google Sheets show it as plain text.
- The file starts with the UTF-8 marker that Excel needs to show Vietnamese letters correctly.
- The note next to the button reads exactly: `The file can contain customers' personal details.`
- The button reads exactly `Export CSV`, like the "Export JSON" button of the Dashboard.
- Example of a file with two reviews:

| Location | Rating | Review text | Date |
|---|---|---|---|
| Riverside | 4 | Friendly staff, but we waited 20 minutes | 2026-10-14 09:30 |
| Riverside | 2 | Too noisy, and the room was cold | 2026-10-12 07:45 |

## What exists today

1. Open the Reviews page (`/reviews/`) of the dev environment, using "Reviews" in the left menu.
2. Observe: filters for location, rating and week, and a table with the columns Location, Rating, Review text, Sentiment and Date, 20 reviews per page. The space at the top right is empty.
3. Observe what is missing: there is no way to take the reviews out of the page. The only way is to copy them by hand. The Dashboard has an "Export JSON" button for its scores, but the Reviews page has no export.

## How to check it when built

1. Open the Reviews page and click "Export CSV" with no filter. Open the downloaded file in Excel.
2. Compare the number of rows (without the header) with the number under the table, "Showing 1-20 of N reviews": they must be the same.
3. Check that the note "The file can contain customers' personal details." is next to the button.
4. Choose a location and "Bad (1-2 stars)", click Apply, click "Export CSV", and check that the file holds only that location's reviews rated 1 or 2.
5. Go to page 2 of a long list and click "Export CSV": the file must hold all matching reviews, not only page 2.
6. Choose a week in which nothing was written, export, and check that the file has only the header row.
7. Add a review whose text starts with `=` (for example `=1+1`), export, and check that Excel shows `=1+1` as text and not `2`.
8. Check in Excel and in Google Sheets that Vietnamese letters are correct and that a review with a comma stays in one cell.

## Expected result

The downloaded file holds exactly the reviews the table would show for the chosen filters, newest first, with the four columns and the full review text. It opens correctly in Excel and Google Sheets, and no review text is ever calculated as a formula.

## Open questions

These are assumptions that nobody has vetoed yet. Marcus confirms or changes them.
1. Is there a limit on how many reviews one export may hold? Assumption: no limit (the dev data holds 7 reviews). Owner: Marcus
2. Who may export? Assumption: everyone who can open the Reviews page, because the app has no login today. Owner: Marcus
3. Should the file have a Sentiment column? Assumption: no, because it follows from the Rating. Owner: Marcus

## Environment

To be checked on the dev environment first.

## Attachments

Sketch of the button position from the reporter, still to be added.

## Implementation notes

- The export is a streamed response (`StreamingHttpResponse`, rows read with `.iterator()`), so a long list never sits in memory and no background job is needed.
- The Reviews page and the export share one filter rule (`resolve_selection`), so the file always holds what the table would show, without the paging.
- The single quote rule also covers a text that starts with a tab or a carriage return, and it applies to the Location cell as well as the Review text.
- Open questions 1 to 3 keep their assumptions until Marcus answers. Without a login, anyone who can open the Reviews page can download customers' personal details; this is the accepted risk behind the note next to the button.
