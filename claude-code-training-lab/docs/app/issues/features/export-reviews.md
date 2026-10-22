# [FEAT] Export reviews to a spreadsheet file

- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-22
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `needs-info`

## Summary

As a manager, I want to download the reviews I see on the Reviews page as a spreadsheet file, so that I can share them with my team and use them in the weekly meeting without copying them by hand. It changes the existing **Reviews** page (`/reviews/`) by adding one button; it does not add a page.

## Scope

- An "Export to CSV" button in the top right of the Reviews page, where the Dashboard has its "Export JSON" button.
- A downloaded file with the reviews that match the filters chosen on the page.

## Not in scope

- Other file types (Excel, PDF).
- Exporting the Dashboard scores (the Dashboard already has its own "Export JSON" button).
- Sending the file by email or on a schedule.
- Choosing which columns go into the file.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a manager clicks "Export to CSV" on the Reviews page without any filter, the screen must offer a download of a file that holds every review, newest first.
- When a manager clicks "Export to CSV" while a location, a rating or a week is chosen, the screen must offer a download of only the reviews that match all chosen filters, in the same order as the table. (proposal)
- When the file is downloaded, the screen must name it `reviews-<date of the download>.csv`, for example `reviews-2026-10-22.csv`. (proposal)
- When a manager clicks "Export to CSV", the screen must offer a file with one header row and one row per review, with the columns Location, Rating, Review text and Date, in this order, and Vietnamese letters that a spreadsheet program shows correctly. (proposal)
- When there is nothing to show because no review matches the filters, the screen must still offer a file that holds only the header row. (proposal)
- When a manager is on page 2 or later of the table and clicks "Export to CSV", the screen must offer a file with all matching reviews, not only the 20 shown on that page.

## Scenarios

**Scenario 1: export one location**
- Given Riverside has 3 reviews: rated 4 on 2026-10-14 at 09:30, rated 5 on 2026-10-13 at 18:05 and rated 2 on 2026-10-12 at 07:45 (Vietnam time), and the other locations have more reviews
- When the manager chooses Riverside on the Reviews page, clicks Apply, then clicks "Export to CSV"
- Then a file `reviews-2026-10-22.csv` is downloaded with the header row and exactly 3 review rows, newest first

**Scenario 2: nothing matches**
- Given no review of Riverside was written in the week of 2026-10-05
- When the manager chooses Riverside and that week, clicks Apply, then clicks "Export to CSV"
- Then a file is downloaded with the header row only

## Spec

- Columns, in order: `Location`, `Rating`, `Review text`, `Date`.
- Rating is the number of stars, 1 to 5.
- Review text is the complete text, not the shortened text shown in the table.
- Date is the day and time in Vietnam time, written `2026-10-14 09:30`.
- Rows are ordered newest first, the same as the table.
- Text that contains a comma, a quotation mark or a new line must not break the columns of the file.
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

1. Open the Reviews page and click "Export to CSV" with no filter. Open the downloaded file in a spreadsheet program.
2. Compare the number of rows (without the header) with the number under the table, "Showing 1-20 of N reviews": they must be the same.
3. Choose a location and "Bad (1-2 stars)", click Apply, click "Export to CSV", and check that the file holds only that location's reviews rated 1 or 2.
4. Go to page 2 of a long list and click "Export to CSV": the file must hold all matching reviews, not only page 2.
5. Choose a week in which nothing was written, export, and check that the file has only the header row.

## Expected result

The downloaded file holds exactly the reviews the table would show for the chosen filters, newest first, with the four columns and the full review text, and it opens correctly in a spreadsheet program.

## Open questions

1. Should the export follow the chosen filters, or always hold every review? Proposal: follow the filters. Owner: Marcus
2. Reviews may contain customers' names or phone numbers. May the file contain the full text, or must personal details be removed? Proposal: full text, and the manager is told it may contain personal details. Owner: Marcus
3. Which spreadsheet program do managers use (Excel, Google Sheets, Numbers)? It decides how Vietnamese letters must be saved. Proposal: Excel and Google Sheets must both show the letters correctly. Owner: Marcus
4. Is there a limit on how many reviews one export may hold? Proposal: no limit for now. Owner: Marcus
5. Who may export? Proposal: everyone who can open the Reviews page. Owner: Marcus

## Environment

To be checked on the dev environment first.

## Attachments

Sketch of the button position from the reporter, still to be added.
